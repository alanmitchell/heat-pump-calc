"""This module provides static information from the AkWarm Energy Library
and from TMY3 files.
When this module is imported, it reads data from files in the 
'data' directory located in this folder and reads some remotely stored
data files via HTTP requests.  The data is stored as module-level
variables and made available to other modules via functions.
See the bottom is file for documentation of those datasets.
"""
import os
import io
import math
import functools
import urllib

import pandas as pd
import numpy as np
import requests

# Most of the data files are located remotely and are retrieved via
# an HTTP request.  The function below is used to retrieve the files,
# which are Pandas DataFrames

# The base URL to the site where the remote files are located
base_url = 'http://ak-energy-data.analysisnorth.com/'

# They also can be pulled from the GitHub repo using the rawgit.com service.
# The advantage is that you point to a particular commit, so the files and their
# structure will never change.
#base_url = 'https://cdn.rawgit.com/alanmitchell/ak-energy-admin/75db23ba/data/'

def get_df(file_path):
    """Returns a Pandas DataFrame that is found at the 'file_path'
    below the Base URL for accessing data.  The 'file_path' should end
    with '.pkl' and points to a pickled, compressed (bz2), Pandas DataFrame.
    """
    b = requests.get(urllib.parse.urljoin(base_url, file_path)).content
    df = pd.read_pickle(io.BytesIO(b), compression='bz2')
    return df

# -----------------------------------------------------------------
# Functions to provide the library data to the rest of the
# application.
def cities():
    """List of all (city name, city ID), alphabetically sorted.
    """
    city_list = list(zip(df_city.Name, df_city.index))
    city_list.sort()   # sorts in place; returns None
    return city_list

def city_from_id(city_id):
    """Returns a Pandas series containing the city information for the City
    identified by 'city_id'.
    """
    return df_city.loc[city_id]

def fuel_price(fuel_id, city_id):
    """Returns the fuel price for the fuel identified by the ID of 
    'fuel_id' for the city identified by 'city_id'.
    """
    city = df_city.loc[city_id]
    fuel = df_fuel.loc[fuel_id]
    if type(fuel.price_col) == str:
        return city[fuel.price_col]
    else:
        # Price column is a NaN and not present for electricity
        return math.nan

def utilities():
    """List of all (utility rate name, utility ID) for all utility rate
    structures, sorted by utility rate name.
    """
    util_list =  list(zip(df_util.Name, df_util.index))
    util_list.sort()
    return util_list

def util_from_id(util_id):
    """Returns a Pandas series containing all of the Utility information for
    the Utility identified by util_id.
    """
    return df_util.loc[util_id]

def miscellaneous_info():
    """Returns the Miscellaneous information stored in the AkWarm Library.
    """
    return misc_info

def effic_cutoff(zone_type):
    """Returns the HSPF cutoff for determinig whether a heat pump is qualified
    as efficient or not. 'zone_type' is 'Single' for 'Multi', which affects the
    cutoff.
    """
    return 12.5 if zone_type=='Single' else 11.0

def heat_pump_manufacturers(zones, efficient_only=False):
    """Returns the list of heat pump manufacturers, sorted alphabetically.
    Returns only the manufacturers of efficient models if 'efficient_only' is True.
    """
    q_str = 'zones == @zones'
    if efficient_only:
        hspf_cutoff = effic_cutoff(zones)
        q_str += ' and hspf >= @hspf_cutoff'
    brands = df_heatpumps.query(q_str).brand.unique()
    return sorted(brands)
    
def heat_pump_models(manufacturer, zones, efficient_only=False):
    """Returns a list of heat pump models (two-tuple: description, id) that
    are from 'manufacturer' and have the zonal type of 'zones' (which has values
    of either 'Single' or 'Multi'.  If 'efficient_only' is True, only efficient models are
    returned.
    """
    q_str = 'brand == @manufacturer and zones == @zones'
    if efficient_only:
        hspf_cutoff = effic_cutoff(zones)
        q_str += ' and hspf >= @hspf_cutoff'
    model_list = []
    df_models = df_heatpumps.query(q_str).sort_values(['capacity_5F_max', 'hspf'], ascending=[True, False])
    for ix, r in df_models.iterrows():
        lbl = f'{r.capacity_5F_max:,.0f} Btu/hr Max at 5°F | HSPF {r.hspf} | Out: {r.outdoor_model} | In: {r.indoor_model}'
        model_list.append((lbl, ix))
    return model_list

def heat_pump_from_id(hp_id):
    """Returns a Pandas series containing information about the heat pump identified by
    the ID of 'hp_id'.  If 'hp_id' is a negative value, this method returns the characteristics
    of a generic heat pump that serves -hp_id heads.  So, if 'hp_id' is -2, characteristics
    of a two-head heat pump is returned.  These generic characteristics have been chosen to
    be close to best-in-class.
    """
    if hp_id >= 0:
        return df_heatpumps.loc[hp_id]
    else:
        # return generic heat pump.  first get a Pandas series object to fill
        # out
        gen_hp = df_heatpumps.iloc[0].copy()
        gen_hp['brand'] =  'Generic'
        gen_hp['ahri_num'] = 0
        gen_hp['zones'] =  'Single' if hp_id == -1 else 'Multi'
        gen_hp['outdoor_model'] =  'Generic'
        gen_hp['indoor_model'] =  'Generic'
        for prop in ('hspf', 'in_pwr_5F_max', 'capacity_5F_max', 'in_pwr_47F_min',
                    'cop_5F_max', 'cop_17F_max', 'cop_47F_max'):
            gen_hp[prop] = np.nan
        if hp_id == -1:
            # Fujitsu 12RLS3
            gen_hp['hspf'] = 14.0
            gen_hp['in_pwr_5F_max'] = 2.1
            gen_hp['capacity_5F_max'] =  16500.0
        elif hp_id == -2:
            # Gree MULTI36HP230V1CO
            gen_hp['hspf'] = 11.5
            gen_hp['in_pwr_5F_max'] = 3.12
            gen_hp['capacity_5F_max'] =  21356.0
        elif hp_id == -3:
            # Mitsubishi Electric PUMY-P36NKMU1
            gen_hp['hspf'] = 11.5
            gen_hp['in_pwr_5F_max'] = 3.695
            gen_hp['capacity_5F_max'] =  29000.0
        elif hp_id == -4:
            # Mitsubishi Electric PUMY-P48NKMU1
            gen_hp['hspf'] = 11.7
            gen_hp['in_pwr_5F_max'] = 4.849
            gen_hp['capacity_5F_max'] =  36400.0

        return gen_hp

def fuels():
    """Returns a list of (fuel name, fuel ID) for all fuels.
    """
    fuel_list = list(zip(df_fuel.desc, df_fuel.index))
    return fuel_list

def fuel_from_id(fuel_id):
    """Returns a Pandas Series of fuel information for the fuel with
    and ID of 'fuel_id'
    """
    return df_fuel.loc[fuel_id]

@functools.lru_cache(maxsize=50)    # caches the TMY dataframes cuz retrieved remotely
def tmy_from_id(tmy_id):
    """Returns a DataFrame of TMY data for the climate site identified
    by 'tmy_id'.
    """
    df = get_df(f'wx/tmy3/proc/{tmy_id}.pkl')
    return df

def heating_design_temp(tmy_id):
    """Returns the heating design temperature (deg F) for the TMY3 site
    identified by 'tmy_id'.
    """
    return df_tmy_meta.loc[tmy_id].heating_design_temp
    
# -----------------------------------------------------------------
# Key datasets are read in here and are available as module-level
# variables for use in the functions above.

# import time
# st = time.time()

# Determine the directory where the local data files are located
this_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(this_dir, 'data')

# read in the DataFrame that describes the available TMY3 climate files.
df_tmy_meta = get_df('wx/tmy3/proc/tmy3_meta.pkl')

# Read in the other City and Utility Excel files.
df_city = get_df('city-util/proc/city.pkl')

# Retrieve the Miscellaneous Information and store into a Pandas Series.
misc_info = get_df('city-util/proc/misc_info.pkl')

# Retrive the list of utilities
df_util = get_df('city-util/proc/utility.pkl')

# Retrive list of Heat Pumps
df_heatpumps = get_df('heat-pump/proc/hp_specs.pkl')

# Retrieve the Fuel information and store in a DataFrame
df_fuel = pd.read_excel(os.path.join(data_dir, 'Fuel.xlsx'), index_col='id')
df_fuel['btus'] = df_fuel.btus.astype(float)

# Change the Efficiency choices column into a Python list (it is a string
# right now.)
df_fuel['effic_choices'] = df_fuel.effic_choices.apply(eval)

# -------------------------------------------------------------------------------------
# For documentation of the remotely acquired DataFrames, see:
# http://ak-energy-data.analysisnorth.com/

# For the df_fuel DataFrame, here is a sample row:
# The Index is the 'id' of fuel
#
# desc                                                   Natural Gas
# unit                                                           ccf
# btus                                                        103700
# co2                                                            117
# price_col                                                 GasPrice
# effic_choices    [(Standard, 80), (High Efficiency Condensing, ...

# print(time.time() - st)