import inspect

import numpy as np

from . import library as lib

class HomeHeatModel(object):
    
    def __init__(self,
                 city_id,
                 hp_model_id,
                 exist_heat_fuel_id,
                 exist_heat_effic,
                 exist_kwh_per_mmbtu,     # Boiler: 5.5, Toyo: 3, Oil Furnace: 8.75 - 15
                 exist_is_point_source,
                 co2_lbs_per_kwh,
                 low_temp_cutoff,
                 garage_stall_count,
                 garage_heated_by_hp,
                 bldg_floor_area,
                 indoor_heat_setpoint,
                 insul_level,             # 1 - 2x4, 2 - 2x6, 3 - better than 2x6 Walls
                 indoor_high_mount,
                 pct_exposed_to_hp,
                 doors_open_to_adjacent,
                 bedroom_temp_tolerance,     # 1 - no temp drop in back rooms, 2 - 4 deg F cooler, 10 deg F cooler

                 # The inputs below are not user inputs, they control the 
                 # calculation process. They are give default values.
                 hp_only=False,           # when using heat pump, it's the only heat source for home
                 no_heat_pump_use=False,  # If True, models existing heating system alone.
                 ua_true_up=1.0,          # used to true up calculation to actual fuel use
                ):
        
        # Store all of these input parameters as object attributes
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        for arg in args[1:]:
            setattr(self, arg, values[arg])

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
    
    # ------- Data needed for calculation of COP vs. Temperature
    
    # Piecewise linear COP vs. outdoor temperature.
    COP_vs_TEMP = (
        (-20.0, 1.1),
        (0.0, 2.0),
        (10.0, 2.2),
        (15.0, 2.3),
        (20.0, 2.5),
        (25.0, 2.7),
        (30.0, 2.8),
        (40.0, 3.0),
        (50.0, 3.2)
    )

    # convert to separate lists of temperatures and COPs
    TEMPS_FIT, COPS_FIT = tuple(zip(*COP_vs_TEMP))

    # The HSPF value that this curve is associated with
    BASE_HSPF = 13.3
    
    # -------------- OTHER CONSTANTS ---------------
    
    GARAGE_HEATING_SETPT = 55.0    # deg F
    
    # ---------------- Main Calculation Method --------------------
    
    def calculate(self):
        """Main calculation routine that models the home and determines
        loads and fuel use by hour.  Also calculates summary results.
        """
        # Set up some shortcut variables to shorten calculation code
        s = self
        
        # ------ Create object variables from the input IDs
        s.city = lib.city_from_id(s.city_id)
        s.hp_model = lib.heat_pump_from_id(s.hp_model_id)
        s.exist_heat_fuel = lib.fuel_from_id(s.exist_heat_fuel_id)
        
        # ------ Make a DataFrame with hourly input information
        # Do as much processing at this level using array operations, as
        # opposed to processing within the hourly loop further below.
        
        df_tmy = lib.tmy_from_id(self.city.TMYid)
        s.df_hourly = df_tmy[['db_temp']].copy()
        # and now make a shorthand variable for this DataFrame
        dfh = s.df_hourly
        dfh['day_of_year'] = dfh.index.dayofyear
        dfh['month'] = dfh.index.month

        # Determine days that the heat pump is running.  Look at the minimum
        # temperature for the day, and ensure that it is above the low 
        # temperature cutoff.
        hp_is_running = lambda x: (x.min() > self.low_temp_cutoff)
        dfh['running'] = dfh.groupby('day_of_year')['db_temp'].transform(hp_is_running)

        # Determine a heat pump COP for each hour. To adjust for the actual indoor
        # setpoint and adjust for the mounting height of the indoor units, adjust the
        # outdoor temperature before applying the COP vs. Outdoor Temperature curve.
        # The COP curve is estimated to be based on a 70 deg F indoor temperature and
        # high mounting of the indoor units.  Give a 2.5 deg F credit for low mounting of
        # the indoor units.
        out_t_adj = (70.0 - s.indoor_heat_setpoint)
        if s.indoor_high_mount == False:
            out_t_adj += 2.5
        cop_interp = np.interp(dfh.db_temp + out_t_adj, 
                               HomeHeatModel.TEMPS_FIT, 
                               HomeHeatModel.COPS_FIT)
        dfh['cop'] = cop_interp * self.hp_model.hspf / HomeHeatModel.BASE_HSPF

        # adjustment to UA for insulation level.  My estimate, accounting
        # for better insulation *and* air-tightness as you move up the 
        # insulation scale.
        ua_insul_adj_arr = np.array([1.25, 1.0, 0.75])   # the adjustment factors by insulation level
        ua_insul_adj = ua_insul_adj_arr[s.insul_level - 1]   # pick the appropriate one
        
        # The UA values below are Btu/hr/deg-F
        # This is the UA / ft2 of the Level 2 (ua_insul_adj = 1) home
        # for the main living space.  Assume garage UA is about 10% higher
        # due to higher air leakage.
        # Determined this UA/ft2 below by modeling a typical Enstar home
        # and having the model estimate space heating use of about 1250 CCF.
        # See 'accessible_UA.ipynb'.
        ua_per_ft2 = 0.189
        ua_home = ua_per_ft2 * ua_insul_adj * s.bldg_floor_area * s.ua_true_up
        garage_area = (0, 14*22, 22*22, 36*25, 48*28)[s.garage_stall_count]
        ua_garage = ua_per_ft2 * 1.1 * ua_insul_adj * garage_area * s.ua_true_up
        
        # Save these UA values as object attributes
        s.ua_home = ua_home
        s.ua_garage = ua_garage

        # Balance Points of main home and garage
        # Assume a 10 deg F internal/solar heating effect for Level 2 insulation
        # in the main home and a 5 deg F heating effect in the garage.
        # Adjust the heating effect accordingly for other levels of insulation.
        htg_effect = np.array([10., 10., 10.]) / ua_insul_adj_arr
        balance_point_home = s.indoor_heat_setpoint - htg_effect[s.insul_level - 1]
        htg_effect = np.array([5.0, 5.0, 5.0]) / ua_insul_adj_arr  # fewer internal/solar in garage
        balance_point_garage = HomeHeatModel.GARAGE_HEATING_SETPT - htg_effect[s.insul_level - 1]

        # BTU loads in the hour for the heat pump and for the secondary system.
        hp_load = []
        secondary_load = []

        # More complicated calculations are done in this hourly loop.  If processing
        # time becomes a problem, try to convert the calculations below into array
        # operations that can be done outside the loop.
        s.max_hp_reached = False       # tracks whether heat pump max output has been reached.
        for h in dfh.itertuples():
            # calculate total heat load for the hour.
            # Really need to recognize that delta-T to outdoors is lower in the adjacent and remote spaces
            # if there heat pump is the only source of heat.
            home_load = max(0.0, balance_point_home - h.db_temp) * ua_home 
            garage_load = max(0.0, balance_point_garage - h.db_temp) * ua_garage
            total_load = home_load + garage_load
            if not h.running or s.no_heat_pump_use:
                hp_load.append(0.0)
                secondary_load.append(total_load)
            else:
                max_hp_output = s.hp_model.in_pwr_5F_max * h.cop * 3412.
                if s.hp_only:
                    hp_ld = min(home_load + garage_load * s.garage_heated_by_hp, max_hp_output)                    
                    hp_load.append(hp_ld)
                    secondary_load.append(total_load - hp_load)
                else:
                    # Nowhere near correct yet.  Just get a calc framework working.
                    hp_ld = min(home_load * s.pct_exposed_to_hp + garage_load * s.garage_heated_by_hp, max_hp_output)
                    hp_load.append(hp_ld)
                    secondary_load.append(total_load - hp_ld)
                if hp_ld >= max_hp_output * 0.999:
                    # running at within 0.1% of maximum heat pump output.
                    s.max_hp_reached = True

        dfh['hp_load_mmbtu'] = np.array(hp_load) / 1e6
        dfh['secondary_load_mmbtu'] = np.array(secondary_load) / 1e6

        # reduce the secondary load to account for the heat produced by the auxiliary electricity
        # use.
        # convert the auxiliary heat factor for the secondary heating system into an
        # energy ratio of aux electricity energy to heat delivered.
        aux_ratio = s.exist_kwh_per_mmbtu * 0.003412
        dfh['secondary_load_mmbtu'] /= (1.0 + aux_ratio)

        # using array operations, calculate kWh use by the heat pump and 
        # the Btu use of secondary system.
        dfh['hp_kwh'] = dfh.hp_load_mmbtu / dfh.cop / 0.003412
        dfh['secondary_fuel_mmbtu'] = dfh.secondary_load_mmbtu / s.exist_heat_effic
        dfh['secondary_kwh'] = dfh.secondary_load_mmbtu * s.exist_kwh_per_mmbtu  # auxiliary electric use

        # Store annual and monthly totals.
        # Annual totals is a Pandas Series.
        total_cols = ['hp_load_mmbtu', 'secondary_load_mmbtu', 'hp_kwh', 'secondary_fuel_mmbtu', 'secondary_kwh']
        s.df_monthly = dfh.groupby('month')[total_cols].sum()
        dfm = s.df_monthly    # shortcut variable
        
        # Add in a column for the peak heat pump demand during the month
        dfm['hp_kw'] = dfh.groupby('month')[['hp_kwh']].max()
        
        # physical units for secondary fuel
        fuel = self.exist_heat_fuel
        dfm['secondary_fuel_units'] = dfm['secondary_fuel_mmbtu'] / fuel.btus * 1e6

        # COP by month
        dfm['cop'] = dfm.hp_load_mmbtu / (dfm.hp_kwh * 0.003412)   

        # Total kWh, heat pump + auxiliary of secondary system
        dfm['total_kwh'] = dfm.hp_kwh + dfm.secondary_kwh
                    
        # Total lbs of CO2 per month, counting electricity and fuel
        dfm['co2_lbs'] = dfm.total_kwh * s.co2_lbs_per_kwh + dfm.secondary_fuel_mmbtu * fuel.co2

        # Change index to Month labels
        s.df_monthly.index = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        s.ser_annual = s.df_monthly.sum().drop(['cop'])
        # Add the seasonal COP to the annual results
        tot = s.ser_annual
        if tot.hp_kwh:
            s.ser_annual['cop'] =  tot.hp_load_mmbtu * 1e6 / tot.hp_kwh / 3412.
        else:
            s.ser_annual['cop'] = np.nan
        
    def monthly_results(self):
        """Returns a DataFrame of monthly results.
        """
        return self.df_monthly
    
    def annual_results(self):
        return self.ser_annual
                    
    def design_heat_load(self):
        """Returns the 99% design heat load for the building and the associated
        design temperature, including the garage if present.  Do not account for 
        any internal or solar gains, as is conventional.
        Return values are Btu/hour and deg F. 
        """
        # get the 1% outdoor temperature
        design_temp = self.df_hourly.db_temp.quantile(0.01)
        design_load = self.ua_home * (self.indoor_heat_setpoint - design_temp) + \
                      self.ua_garage * (HomeHeatModel.GARAGE_HEATING_SETPT - design_temp)
        return design_load, design_temp
    
    def hp_max_capacity_5F(self):
        """Returns the maximum capacity of the heat pump at 5 deg F.  Uses the
        COP curve unless the manufacturer's spec is lower.
        Returns is Btu/hour.
        """
        cop_5F = np.interp(5.0, HomeHeatModel.TEMPS_FIT, HomeHeatModel.COPS_FIT)
        max_from_curve = cop_5F * self.hp_model.in_pwr_5F_max * 3412.
        return min(max_from_curve, self.hp_model.capacity_5F_max)
