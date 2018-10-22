"""Provides a class to model the impact of a heat pump on
energy use and cost.
"""
import inspect
import pandas as pd
import numpy as np

from . import library as lib
from . import elec_cost
from .home_heat_model import HomeHeatModel
from .elec_cost import ElecCostCalc

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

    def __init__(self,
                 city_id,
                 utility,
                 co2_lbs_per_kwh,
                 exist_heat_fuel_id,
                 exist_unit_fuel_cost,
                 exist_fuel_use,
                 exist_heat_effic,
                 exist_kwh_per_mmbtu,
                 exist_is_point_source,
                 includes_dhw,
                 includes_dryer,
                 includes_cooking,
                 occupant_count,
                 elec_use_jan,
                 elec_use_may,
                 hp_model_id,
                 indoor_high_mount,
                 low_temp_cutoff,
                 garage_stall_count,
                 garage_heated_by_hp,
                 bldg_floor_area,
                 indoor_heat_setpoint,
                 insul_level,  
                 pct_exposed_to_hp,
                 doors_open_to_adjacent,
                 bedroom_temp_tolerance,
                 capital_cost,
                 rebate_dol,
                 pct_financed,
                 loan_term,
                 loan_interest,
                 hp_life,
                 op_cost_chg,
                 sales_tax,
                 discount_rate,
                 inflation_rate,
                 fuel_esc_rate,
                 elec_esc_rate,
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
            val = repr(self.__dict__[attr])[:1000]
            if len(val)>70:
                s+=f'\n{attr}:\n{val}\n\n'
            else:
                s += f'{attr}: {val}\n'
        return s
        
    def check_inputs(self):
        pass
        
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
            exist_is_point_source=s.exist_is_point_source,
            co2_lbs_per_kwh=s.co2_lbs_per_kwh,
            low_temp_cutoff=s.low_temp_cutoff,
            garage_stall_count=s.garage_stall_count,
            garage_heated_by_hp=s.garage_heated_by_hp,
            bldg_floor_area=s.bldg_floor_area,
            indoor_heat_setpoint=s.indoor_heat_setpoint,
            insul_level=s.insul_level,            
            pct_exposed_to_hp=s.pct_exposed_to_hp,
            doors_open_to_adjacent=s.doors_open_to_adjacent,
            bedroom_temp_tolerance=s.bedroom_temp_tolerance,    
        )
        
        # Match the existing space heating use if it is provided.  Do so by using
        # the UA true up factor.
        # **** TO DO Deal with Electric Heat.  Calculate a space_fuel_use for electric
        # **** and then use the same calculation below.
        if s.exist_fuel_use is not None:
            
            # Remove DHW and Clothes dryer if they are present in the fuel use
            # number.
            space_fuel_use = s.exist_fuel_use
            if s.includes_dhw:
                dhw_use = s.occupant_count * 4.23e6 / fuel.dhw_effic / fuel.btus
                space_fuel_use -= dhw_use
                
            if s.includes_dryer:
                space_fuel_use -= 2.15e6 * s.occupant_count / fuel.btus
            
            sim.no_heat_pump_use = True
            sim.calculate()
            fuel_use1 = sim.annual_results().secondary_fuel_units
            
            # scale the UA linearly to attempt to match the target fuel use
            ua_true_up = space_fuel_use / fuel_use1
            sim.ua_true_up = ua_true_up
            sim.calculate()
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
        
        # Run the base case with no heat pump and record energy results
        sim.no_heat_pump_use = True
        sim.calculate()
        s.df_mo_en_base = sim.monthly_results()
        
        # Run the model with the heat pump and record energy results
        sim.no_heat_pump_use = False
        sim.calculate()
        s.df_mo_en_hp = sim.monthly_results()
        # record design heat load
        s.summary['design_heat_load'], s.summary['design_heat_temp'] = sim.design_heat_load()
        
        # Calculate some summary measures
        s.summary['cop'] = sim.annual_results().cop
        s.summary['hp_max_capacity_5F'] = sim.hp_max_capacity_5F()
        s.summary['max_hp_reached'] = sim.max_hp_reached
        # CO2 savings
        ann_en_base = s.df_mo_en_base.sum()
        ann_en_hp = s.df_mo_en_hp.sum()
        s.summary['co2_lbs_saved'] = ann_en_base.co2_lbs - ann_en_hp.co2_lbs
        s.summary['co2_driving_miles_saved'] = convert_co2_to_miles_driven(s.summary['co2_lbs_saved'])
        
        # Create DataFrames that hold monthly energy cost amounts
        self.calc_monthly_cash()
        
        # Create a multi-year Cash Flow DataFrame and summary economic measures.
        self.calc_cash_flow()
            
    def calc_monthly_cash(self):
        """Calculates two DataFrames, s.df_mo_dol_base and s.df_mo_dol_hp, that contain
        the fuel and electricity costs in the base case (no heat pump) scenario and the
        with heat pump scenario.  A number of inputs found as object attributes are used. 
        """
        # shortcut to self
        s = self

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
        
        # Start the DataFrames, base and w/ heat pump
        # Each starts with just an index column with the month
        # Make shortcut variables as well.
        s.df_mo_dol_base = dfb = s.df_mo_en_base[[]].copy()
        s.df_mo_dol_hp = dfh = s.df_mo_en_base[[]].copy()
        
        # Make an object to calculate electric utility costs
        elec_cost_calc = ElecCostCalc(s.utility, sales_tax=s.sales_tax, pce_limit=500.0)
        # cost function that will be applied to each row of the cost DataFrame
        cost_func = lambda r: elec_cost_calc.monthly_cost(r.elec_kwh, r.elec_kw)

        dfb['elec_kwh'] =  pat_use
        # rough estimate of a base demand: not super critical, as the demand rate 
        # structure does not have blocks.  Assume a load factor of 0.4
        dfb['elec_kw'] = dfb.elec_kwh / 730.0 / 0.4
        dfb['elec_dol'] = dfb.apply(cost_func, axis=1)

        # Now fuel
        dfb['secondary_fuel_units'] = s.df_mo_en_base.secondary_fuel_units
        dfb['secondary_fuel_dol'] = dfb.secondary_fuel_units * s.exist_unit_fuel_cost * (1. + s.sales_tax)

        # Total Electric + space heat
        dfb['total_dol'] =  dfb.elec_dol + dfb.secondary_fuel_dol

        # Now with the heat pump
        # determine extra kWh used in the heat pump scenario
        extra_kwh = (s.df_mo_en_hp.total_kwh - s.df_mo_en_base.total_kwh).values
        dfh['elec_kwh'] = dfb['elec_kwh'] + extra_kwh
        dfh['elec_kw'] =  dfb['elec_kw'] + s.df_mo_en_hp.hp_kw
        dfh['elec_dol'] = dfh.apply(cost_func, axis=1)

        # Now fuel
        dfh['secondary_fuel_units'] = s.df_mo_en_hp.secondary_fuel_units
        dfh['secondary_fuel_dol'] = dfh.secondary_fuel_units * s.exist_unit_fuel_cost * (1. + s.sales_tax)

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
        
        initial_cost[0] = -s.capital_cost * (1 + s.sales_tax) * (1 - s.pct_financed) + s.rebate_dol
        loan_pmt = np.pmt(s.loan_interest, s.loan_term, s.capital_cost * (1 + s.sales_tax) * s.pct_financed)
        loan_cost = [0.0] + [loan_pmt] * s.loan_term + [0.0] * (s.hp_life -  s.loan_term)
        loan_cost = np.array(loan_cost)
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
        s.summary['elec_use_base'] = ann_base.elec_kwh
        s.summary['elec_use_hp'] =  ann_hp.elec_kwh
        s.summary['elec_use_chg'] = ann_chg.elec_kwh
        s.summary['elec_rate_avg_base'] = ann_base.elec_dol / ann_base.elec_kwh
        s.summary['elec_rate_avg_hp'] = ann_hp.elec_dol / ann_hp.elec_kwh