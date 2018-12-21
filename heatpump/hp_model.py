"""Provides a class to model the impact of a heat pump on
energy use and cost.
"""
from pprint import pformat
import inspect
import pandas as pd
import numpy as np

from . import library as lib
from . import elec_cost
from .home_heat_model import HomeHeatModel
from .elec_cost import ElecCostCalc
from .utils import is_null
from . import ui_helper

# --------- Some Constants

# The days in each month
DAYS_IN_MONTH = np.array([
    31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
])

# The pattern or Lights and appliances other than DHW, Clothes Drying & Cooking.
# This is average power in the month divided average annual power.
LIGHTS_OTHER_PAT = np.array([
    1.13, 1.075, 1.0, 0.925, 0.87, 0.85, 0.87, 0.925, 1.0, 1.075, 1.13, 1.15
])

def make_pattern(esc, life):
    """Makes a numpy array of length (life + 1) containing an escalation pattern
    that starts with a 1.0 in year 1 and escalates at the rate of 'esc' per year.
    """
    pat = np.ones(life - 1) * (1 + esc)
    return np.insert(pat.cumprod(), 0, [0.0, 1.0])

def convert_co2_to_miles_driven(co2_saved):
    """Converts CO2 emissions to a mileage driven
    equivalent for vehicles in the U.S. using EPA
    methodology:  https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references#miles
    """
    pounds_in_metric_ton = 2204.62
    tons_co2_per_gallon = 0.0089
    avg_gas_mileage_us_fleet = 22
    mileage_equivalent = co2_saved / pounds_in_metric_ton / tons_co2_per_gallon * avg_gas_mileage_us_fleet
    
    return mileage_equivalent


class HP_model:

    # Some of inputs parameters are documented in the home_heat_model.HomeHeatModel class constructor;
    # those inputs are marked as such below.
    def __init__(self,
                 city_id,                # see home_heat_model.HomeHeatModel
                 utility,                # The full Pandas Series describing the Electric Utility
                 pce_limit,              # The maximum kWh in a month subsidized by PCE (0 will mean no PCE subsidy)
                 co2_lbs_per_kwh,        # see home_heat_model.HomeHeatModel
                 exist_heat_fuel_id,     # see home_heat_model.HomeHeatModel
                 exist_unit_fuel_cost,   # Cost per physical unit (e.g. gallon, CCF) of the existing space heating fuel.
                 exist_fuel_use,         # Annual existing fuel use for Space Heating and the other end uses identified using that fuel. None if not available.
                 exist_heat_effic,       # see home_heat_model.HomeHeatModel
                 exist_kwh_per_mmbtu,    # see home_heat_model.HomeHeatModel
                 includes_dhw,           # True if the existing Space Heating Fuel type also is used for DHW.
                 includes_dryer,         # True if the existing Space Heating Fuel type also is used for Clothes Drying.
                 includes_cooking,       # True if the existing Space Heating Fuel type also is used for Cooking.
                 occupant_count,         # Number of occupants using DHW, Clothes Drying, Cooking
                 elec_use_jan,           # The electric use in January, prior to heat pump installation, kWh.
                 elec_use_may,           # The electric use in May, prior to heat pump installation, kWh.
                 hp_model_id,            # see home_heat_model.HomeHeatModel
                 low_temp_cutoff,        # see home_heat_model.HomeHeatModel
                 off_months_chks,        # see home_heat_model.HomeHeatModel, parameter 'off_months' there
                 garage_stall_count,     # see home_heat_model.HomeHeatModel
                 garage_heated_by_hp,    # see home_heat_model.HomeHeatModel
                 bldg_floor_area,        # see home_heat_model.HomeHeatModel
                 indoor_heat_setpoint,   # see home_heat_model.HomeHeatModel
                 insul_level,            # see home_heat_model.HomeHeatModel
                 pct_exposed_to_hp,      # see home_heat_model.HomeHeatModel
                 doors_open_to_adjacent, # see home_heat_model.HomeHeatModel
                 bedroom_temp_tolerance, # see home_heat_model.HomeHeatModel
                 capital_cost,           # Initial cost of the heat pump installation
                 rebate_dol,             # Rebate $ received for heat pump installation
                 pct_financed,           # fraction (0 - 1.0) of heat pump installation cost financed by a loan.
                 loan_term,              # Length of loan in years.
                 loan_interest,          # interest rate of loan, expressed as fraction, i.e. 0.1 for 10%.
                 hp_life,                # life of heat pump in years
                 op_cost_chg,            # operating cost increase associated with heat pump (negative if decrease)
                 sales_tax,              # sales tax, expressed as a fraction (0.05 for 5%/yr) that applies to electricity and fuel costs
                 discount_rate,          # economic discount rate, expressed as a fraction, per year. Nominal, not adjusted for inflation.
                 inflation_rate,         # general inflation rate expressed as a fraction, per year.
                 fuel_esc_rate,          # price escalation rate of fuel used for existing heating system, fraction/year, nominal
                 elec_esc_rate,          # price escalation rate of electricity, fraction/year, nominal
                ):

        # Store all of these input parameters as object attributes.
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        for arg in args[1:]:
            setattr(self, arg, values[arg])
            
        # Look up the objects associated with the IDs
        self.city = lib.city_from_id(city_id)
        self.exist_fuel = lib.fuel_from_id(exist_heat_fuel_id)
        self.hp_model = lib.heat_pump_from_id(hp_model_id)
                    
    def __repr__(self):
        """Returns a string with all the object attributes shown.  Text is truncated
        at 1,000 characters for attributes with long representations.
        """
        s = ''
        for attr in self.__dict__:
            val = pformat(self.__dict__[attr])[:1500]
            if len(val)>70:
                s+=f'\n{attr}:\n{val}\n\n'
            else:
                s += f'{attr}: {val}\n'
        return s
        
    def run(self):
        
        # shortcut for self
        s = self
        
        # shortcut to existing heating fuel
        fuel = s.exist_fuel

        # holds summary measures for the heat pump project (e.g. seasonal COP,
        # internal rate of return).  Fill out first item: secondary fuel info.
        s.summary = {'fuel_unit': fuel.unit, 'fuel_desc': fuel.desc}
        
        # Create the home energy simulation object
        sim = HomeHeatModel(
            city_id=s.city_id,
            hp_model_id=s.hp_model_id,
            exist_heat_fuel_id=s.exist_heat_fuel_id,
            exist_heat_effic=s.exist_heat_effic,
            exist_kwh_per_mmbtu=s.exist_kwh_per_mmbtu,    
            co2_lbs_per_kwh=s.co2_lbs_per_kwh,
            low_temp_cutoff=s.low_temp_cutoff,
            off_months=s.off_months_chks,
            garage_stall_count=s.garage_stall_count,
            garage_heated_by_hp=s.garage_heated_by_hp,
            bldg_floor_area=s.bldg_floor_area,
            indoor_heat_setpoint=s.indoor_heat_setpoint,
            insul_level=s.insul_level,
            pct_exposed_to_hp=s.pct_exposed_to_hp,
            doors_open_to_adjacent=s.doors_open_to_adjacent,
            bedroom_temp_tolerance=s.bedroom_temp_tolerance,    
        )

        # If other end uses use the heating fuel, make an estimate of their annual
        # consumption of that fuel.  This figure is expressed in the physical unit
        # for the fuel type, e.g. gallons of oil.  Save this as an object attribute
        # so it is accessible in other routines.  See Evernote notes on values (AkWarm
        # for DHW and Michael Bluejay for Drying and Cooking).
        is_electric = (s.exist_heat_fuel_id == ui_helper.ELECTRIC_ID)  # True if Electric
        s.fuel_other_uses = s.includes_dhw * 4.23e6 / fuel.dhw_effic
        s.fuel_other_uses += s.includes_dryer * (0.86e6 if is_electric else 2.15e6)
        s.fuel_other_uses += s.includes_cooking * (0.64e6 if is_electric else 0.8e6)
        s.fuel_other_uses *= s.occupant_count / fuel.btus

        # For elecric heat we also need to account for lights and other applicances not
        # itemized above.
        if is_electric:
            # Use the AkWarm Medium Lights/Appliances formula but take 25% off
            # due to efficiency improvements since then.
            s.lights_other_elec = 2086. + 1.20 * s.bldg_floor_area   # kWh in the year
        else:
            s.lights_other_elec = 0.0
        
        # Match the existing space heating use if it is provided.  Do so by using
        # the UA true up factor.
        if not is_null(s.exist_fuel_use):
            
            # Remove the energy use from the other end uses that use the fuel
            space_fuel_use = s.exist_fuel_use - s.fuel_other_uses - s.lights_other_elec

            sim.no_heat_pump_use = True
            sim.calculate()
            if is_electric:
                # For electric heat, electric use for space heat is in secondary_kwh
                fuel_use1 = sim.annual_results().secondary_kwh
            else:
                fuel_use1 = sim.annual_results().secondary_fuel_units
            
            # scale the UA linearly to attempt to match the target fuel use
            ua_true_up = space_fuel_use / fuel_use1
            sim.ua_true_up = ua_true_up
            sim.calculate()

            if is_electric:
                # For electric heat, electric use for space heat is in secondary_kwh
                fuel_use2 = sim.annual_results().secondary_kwh
            else:
                fuel_use2 = sim.annual_results().secondary_fuel_units
            
            # In case it wasn't linear, inter/extrapolate to the final ua_true_up
            slope = (fuel_use2 - fuel_use1)/(ua_true_up - 1.0)
            ua_true_up = 1.0 + (space_fuel_use - fuel_use1) / slope

        else:
            ua_true_up = 1.0
            
        # Set the UA true up value into the model and also save it as
        # an attribute of this object so it can be observed.
        sim.ua_true_up = ua_true_up
        s.ua_true_up = ua_true_up
        
        # Run the base case with no heat pump and record energy results.
        # This model only models the space heating end use.
        sim.no_heat_pump_use = True
        sim.calculate()
        s.df_mo_en_base = sim.monthly_results()
        s.ann_en_base = sim.annual_results()
        
        # Run the model with the heat pump and record energy results
        sim.no_heat_pump_use = False
        sim.calculate()
        s.df_mo_en_hp = sim.monthly_results()
        s.ann_en_hp = sim.annual_results()
        s.df_hourly = sim.df_hourly

        # record design heat load
        s.summary['design_heat_load'], s.summary['design_heat_temp'] = sim.design_heat_load()
        
        # Calculate some summary measures
        s.summary['cop'] = s.ann_en_hp.cop
        s.summary['hp_max_capacity_5F'] = sim.hp_max_capacity_5F()
        s.summary['max_hp_reached'] = sim.max_hp_reached
        
        # CO2 savings
        s.summary['co2_lbs_saved'] = s.ann_en_base.co2_lbs - s.ann_en_hp.co2_lbs
        s.summary['co2_driving_miles_saved'] = convert_co2_to_miles_driven(s.summary['co2_lbs_saved'])
        s.summary['hp_load_frac'] = s.ann_en_hp.hp_load_mmbtu / (s.ann_en_hp.hp_load_mmbtu + s.ann_en_hp.secondary_load_mmbtu)
        
        # Create DataFrames that hold monthly energy cost amounts
        # Results are stored as object attributes.
        self.calc_monthly_cash()
        
        # Create a multi-year Cash Flow DataFrame and summary economic measures.
        # Results are stored as object attributes.
        self.calc_cash_flow()
            
    def calc_monthly_cash(self):
        """Calculates two DataFrames, s.df_mo_dol_base and s.df_mo_dol_hp, that contain
        the fuel and electricity costs in the base case (no heat pump) scenario and the
        with heat pump scenario.  A number of inputs found as object attributes are used. 
        """
        # shortcut to self
        s = self

        # Start the DataFrames, base and w/ heat pump
        # Each starts with just an index column with the month
        # Make shortcut variables as well.
        s.df_mo_dol_base = dfb = s.df_mo_en_base[[]].copy()
        s.df_mo_dol_hp = dfh = s.df_mo_en_base[[]].copy()

        # Determine the base electric use by month.  Approach is different 
        # if there is electric heat.
        is_electric_heat = (s.exist_heat_fuel_id == ui_helper.ELECTRIC_ID)
        if not is_electric_heat:
            # Fuel-based space heat.
            # The User supplied a January and a May kWh usage value that should
            # be used for the base case (no heat pump) total electricity use.
            # But, need to come up with a kWh value for every month.  Do that by
            # adjusting the kWh pattern available for this city.
            #
            # Determine the multiplier to adjust to the pattern to the actual.
            pat_use = np.array(s.city.avg_elec_usage)
            mult = (s.elec_use_jan - s.elec_use_may) / (pat_use[0] - pat_use[4])
            pat_use = mult * pat_use
            pat_use += s.elec_use_jan - pat_use[0]

            # The electricity use in the base case
            dfb['elec_kwh'] =  pat_use

            # rough estimate of a base demand: not super critical, as the demand rate 
            # structure does not have blocks.  Assume a load factor of 0.4
            dfb['elec_kw'] = dfb.elec_kwh / (DAYS_IN_MONTH * 24.0) / 0.4

        else:
            # Electric Heat Case
            # No Jan and May values are provided.  Instead we have possibly some
            # DHW, clothes drying, and cooking.  Plus, we have base lights/other appliances.
            # And finally we have the Elecric heat making up the base electric usage.

            # First, DHW, Clothes Drying and Cooking.  Assume flat use through year.
            # This is a numpy array because DAYS_IN_MONTH is an array.
            elec_kwh = s.fuel_other_uses / 8760.0 * DAYS_IN_MONTH * 24.0

            # Now lights and other misc. appliances. Some monthly variation, given
            # by LIGHTS_OTHER_PAT.
            elec_kwh += s.lights_other_elec / 8760.0 * LIGHTS_OTHER_PAT * DAYS_IN_MONTH * 24.0

            # For the peak demand of those two categories of use, just assume 40% load factor.
            elec_kw = elec_kwh / (DAYS_IN_MONTH * 24.0) / 0.4

            # Now add in space heating kWh and kW
            elec_kwh += s.df_mo_en_base.total_kwh.values
            elec_kw += s.df_mo_en_base.total_kw.values

            # store results
            dfb['elec_kwh'] =  elec_kwh
            dfb['elec_kw'] =  elec_kw

        # Make an object to calculate electric utility costs
        elec_cost_calc = ElecCostCalc(s.utility, sales_tax=s.sales_tax, pce_limit=s.pce_limit)
        # cost function that will be applied to each row of the cost DataFrame
        cost_func = lambda r: elec_cost_calc.monthly_cost(r.elec_kwh, r.elec_kw)

        dfb['elec_dol'] = dfb.apply(cost_func, axis=1)

        if not is_electric_heat:
            # Now fuel use by month.  Remember that the home heat model only looked at
            # space heating, so we need to add in the fuel use from the other end uses
            # that use this fuel.
            dfb['secondary_fuel_units'] = s.df_mo_en_base.secondary_fuel_units + \
                s.fuel_other_uses / 12.0
            dfb['secondary_fuel_dol'] = dfb.secondary_fuel_units * s.exist_unit_fuel_cost * (1. + s.sales_tax)
        else:
            # Electric Heat, so no secondary fuel
            dfb['secondary_fuel_units'] = 0.0
            dfb['secondary_fuel_dol'] = 0.0

        # Total Electric + space heat
        dfb['total_dol'] =  dfb.elec_dol + dfb.secondary_fuel_dol

        # Now with the heat pump
        # determine extra kWh used in the heat pump scenario. Note, this will
        # be negative numbers if the base case used electric heat.
        extra_kwh = (s.df_mo_en_hp.total_kwh - s.df_mo_en_base.total_kwh).values
        dfh['elec_kwh'] = dfb['elec_kwh'] + extra_kwh
        extra_kw = (s.df_mo_en_hp.total_kw - s.df_mo_en_base.total_kw).values
        dfh['elec_kw'] =  dfb['elec_kw'] + extra_kw
        dfh['elec_dol'] = dfh.apply(cost_func, axis=1)

        # Now fuel, including other end uses using the heating fuel
        if not is_electric_heat:
            dfh['secondary_fuel_units'] = s.df_mo_en_hp.secondary_fuel_units + \
                s.fuel_other_uses / 12.0
            dfh['secondary_fuel_dol'] = dfh.secondary_fuel_units * s.exist_unit_fuel_cost * (1. + s.sales_tax)
        else:
            # Electric Heat, so no secondary fuel
            dfh['secondary_fuel_units'] = 0.0
            dfh['secondary_fuel_dol'] = 0.0

        # Total Electric + space heat
        dfh['total_dol'] =  dfh.elec_dol + dfh.secondary_fuel_dol
        
    def calc_cash_flow(self):
        """Calculates the cash flow impacts of the installation over the 
        life of the heat pump.  Creates a DataFrame, self.df_cash_flow, that shows
        the impacts. In that DataFrame, postive values are benefits and negative 
        values are costs. 
        Also calculates some summary economic measures that are added to
        the self.summary dictionary.
        """
        s = self   # shortcut variable

        # determine the changes caused by the heat pump on an annual basis.
        # First calculate annual totals for base case and heat pump case and
        # then calculate the change.
        ann_base = s.df_mo_dol_base.sum()
        ann_hp = s.df_mo_dol_hp.sum()
        ann_chg = ann_hp - ann_base
        initial_cost = np.zeros(s.hp_life+1)
        
        # Am not automatically adding sales tax to the initial cost as the user was
        # supposed to includes sales tax in their input.
        initial_cost[0] = -s.capital_cost * (1 - s.pct_financed) + s.rebate_dol
        loan_pmt = np.pmt(s.loan_interest, s.loan_term, s.capital_cost * s.pct_financed)
        if loan_pmt < -0.01:   # loan payment is negative
            loan_cost = [0.0] + [loan_pmt] * s.loan_term + [0.0] * (s.hp_life -  s.loan_term)
            loan_cost = np.array(loan_cost)
        else:
            loan_cost = 0.0
        op_cost = -s.op_cost_chg * make_pattern(s.inflation_rate, s.hp_life)
        fuel_cost = -ann_chg.secondary_fuel_dol * make_pattern(s.fuel_esc_rate, s.hp_life)
        elec_cost = -ann_chg.elec_dol * make_pattern(s.elec_esc_rate, s.hp_life)
        cash_flow = initial_cost + loan_cost + op_cost + fuel_cost + elec_cost

        # calculate cumulative, discounted cash flow.
        disc_factor = np.ones(s.hp_life) * (1 + s.discount_rate)
        disc_factor = np.insert(disc_factor.cumprod(), 0, 1.0)
        cum_disc_cash_flow = np.cumsum(cash_flow / disc_factor)
                
        s.df_cash_flow = pd.DataFrame(
            {'initial_cost': initial_cost,
             'loan_cost': loan_cost,
             'op_cost': op_cost,
             'fuel_cost': fuel_cost,
             'elec_cost': elec_cost,
             'cash_flow': cash_flow,
             'cum_disc_cash_flow': cum_disc_cash_flow,
            }
        )
        s.df_cash_flow.index.name = 'year'
        
        # Calculate IRR and NPV for w/ and w/o PCE.
        s.summary['irr'] = np.irr(s.df_cash_flow.cash_flow)
        s.summary['npv'] = np.npv(s.discount_rate, s.df_cash_flow.cash_flow)
        
        # Add some summary fuel and electric usage  and unit cost info
        s.summary['fuel_use_base'] = ann_base.secondary_fuel_units
        s.summary['fuel_use_hp'] =  ann_hp.secondary_fuel_units
        s.summary['fuel_use_chg'] = ann_chg.secondary_fuel_units
        if ann_chg.secondary_fuel_units != 0.0:
            s.summary['fuel_price_incremental'] = ann_chg.secondary_fuel_dol / ann_chg.secondary_fuel_units
        else:
            s.summary['fuel_price_incremental'] = np.nan
        s.summary['elec_use_base'] = ann_base.elec_kwh
        s.summary['elec_use_hp'] =  ann_hp.elec_kwh
        s.summary['elec_use_chg'] = ann_chg.elec_kwh
        s.summary['elec_rate_avg_base'] = ann_base.elec_dol / ann_base.elec_kwh
        s.summary['elec_rate_avg_hp'] = ann_hp.elec_dol / ann_hp.elec_kwh
        s.summary['elec_rate_incremental'] = ann_chg.elec_dol / ann_chg.elec_kwh
    