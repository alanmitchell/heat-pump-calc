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
import functools
import urllib

import pandas as pd
import requests

# Most of the data files are located remotely and are retrieved via
# an HTTP request.  The function below is used to retrieve the files,
# which are Pandas DataFrames

# The base URL to the site where the remote files are located
base_url = 'http://ak-energy-data.analysisnorth.com/'

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
    return city[fuel.price_col]

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

def heat_pump_manufacturers(popular_only=False):
    """Returns the list of heat pump manufacturers, sorted alphabetically.
    Returns only the manufacturers of popular models if 'popular_only' is True.
    """
    if popular_only:
        return list(df_heatpumps.query('popular == True').brand.unique())
    else:
        return list(df_heatpumps.brand.unique())

def heat_pump_models(manufacturer, zones, popular_only=False):
    """Returns a list of heat pump models (two-tuple: description, id) that
    are from 'manufacturer' and have the zonal type of 'zones' (which has values
    of either 'Single' or 'Multi'.  If popular_only is True, only popular models are
    returned.
    """
    q_str = 'brand == @manufacturer and zones == @zones'
    if popular_only:
        q_str += ' and popular == True'
    model_list = []
    df_models = df_heatpumps.query(q_str).sort_values('capacity_5F_max')
    for ix, r in df_models.iterrows():
        lbl = f'Outdoor: {r.outdoor_model} Indoor: {r.indoor_model}, Max at 5 °F = {r.capacity_5F_max:,.0f} Btu/hr, HSPF = {r.hspf}'
        model_list.append((lbl, ix))
    return model_list

def heat_pump_from_id(hp_id):
    """Returns a Pandas series containing information about the heat pump identified by
    the ID of 'hp_id'.
    """
    return df_heatpumps.loc[hp_id]

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

# -----------------------------------------------------------------
# Key datasets are read in here and are available as module-level
# variables for use in the functions above.

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

# -------------------------------------------------------------------------------------
# For documentation of the remotely acquired DataFrames, see:
# http://ak-energy-data.analysisnorth.com/

# For the df_fuel DataFrame, here is a sample row:
# The Index is the 'id' of fuel
#
# desc         Natural Gas
# unit                 ccf
# btus              103700
# co2                  117
# effic                0.8
# price_col       GasPrice

