"""This module provides static information from the AkWarm Energy Library
and from TMY3 files.
When this module is imported, it reads data from CSV files in the 
'data' directory located in this folder and processes that data into
a more useable form.  This processing code is located near the bottom of
this module, after all of the functions that provide the data to the 
rest of the application.  At the very bottom of this module is a description
of module-level DataFrames created by the preprocessing that are available
to the other functions in this module.
"""
import os
import csv
from datetime import datetime
import pickle
import math
from enum import Enum

import pandas as pd
import numpy as np

from utils import chg_nonnum

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

def util_from_id(util_id):
    """Returns a Pandas series containing all of the Utility information for
    the Utility identified by util_id.
    """
    return df_util.loc[util_id]

def miscellaneous_info():
    """Returns the Miscellaneous information stored in the AkWarm Library.
    """
    return misc_info

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

def tmy_from_id(tmy_id):
    """Returns a DataFrame of TMY data for the climate site identified
    by 'tmy_id'.
    """
    df = pd.read_pickle(os.path.join(data_dir, 'climate/{}.pkl'.format(tmy_id)))
    return df

# -----------------------------------------------------------------
# One-time Processing of AkWarm CSV data occurs here when this
# module is imported.
# Final products of the processing are described at the bottom
# of the code and are available as module-level variables to the
# functions above.

# First, some functions needed for processing

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between a point on earth
    and an array of other points.  Lat/Lon in decimal degrees.
    lat1 & lon1 are the single point, lat2 and lon2 are numpy
    arrays.
    """
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2. * np.arcsin(np.sqrt(a))
    km = 6367. * c
    return km

def closest_tmy(city_ser, dft):
    """Finds the closest TMY3 site, and returns ID and City, State name of
    that TMY3 site.  'city_ser' is a Pandas Series describing the city, and 'dft'
    is a DataFrame of meta data describing the possible TMY sites. 
    """
    dists = haversine(city_ser.Latitude, city_ser.Longitude, dft.latitude, dft.longitude)
    closest_id = dists.idxmin()
    tmy_site = dft.loc[closest_id]
    return closest_id, '{}, {}'.format(tmy_site.city, tmy_site.state)

# Determine the directory where the CSV files are located.
this_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(this_dir, 'data')

# read in the DataFrame that describes the available TMY3 climate files.
df_tmy_meta = pd.read_pickle(os.path.join(data_dir, 'climate/tmy3_meta.pkl'))

# Read in the other City and Utility CSV files.
# The Utility.csv had non-ASCII characters in it.  You can either read with 
# "engine='python' " in the 'read_csv()' command, or you can clean up the
# file with:  tr -cd '\11\12\15\40-\176' < file-with-binary-chars > clean-file
# I did both.
# The problem with Line 467 in the Utility.csv file in the Notes field.  That
# field started with a non-ASCII character.
df_city = pd.read_csv(os.path.join(data_dir, 'City.csv'), engine='python')

df_city_util_link = pd.read_csv(os.path.join(data_dir, 'City_Utility_Links.csv'), engine='python')

# Retrieve the Miscellaneous Information and store into a Pandas Series.
misc_info = pd.read_csv(os.path.join(data_dir, 'Misc_Info.csv'), engine='python').iloc[0]

df_util = pd.read_csv(os.path.join(data_dir, 'Utility.csv'), engine='python') 
df_util.ID = df_util.ID.astype(int)
df_util.drop(['SiteSourceMultiplierOverride', 'BuybackRate', 'Notes'], axis=1, inplace=True)
df_util.index = df_util.ID
df_util['NameShort'] = df_util['Name'].str[:6]

# make a list of blocks with rates for each utility and save that as
# a column in the DataFrame.
blocks_col = []
for ix, util in df_util.iterrows():
    adjust = chg_nonnum(util.FuelSurcharge, 0.0) + chg_nonnum(util.PurchasedEnergyAdj, 0.0)
    if util.ChargesRCC:
        adjust += chg_nonnum(misc_info.RegSurchargeElectric, 0.0)
    blocks = []
    for blk in range(1, 6):
        block_kwh = chg_nonnum(util['Block{}'.format(blk)], math.nan)
        block_rate = chg_nonnum(util['Rate{}'.format(blk)], math.nan)
        if not math.isnan(block_rate):
            block_rate += adjust
        blocks.append((block_kwh, block_rate))
    blocks_col.append(blocks)
df_util['Blocks'] = blocks_col

df_city = df_city.query('Active == 1')[[
    'ID',
    'Name',
    'Latitude',
    'Longitude',
    'ERHRegionID',
    'WAPRegionID',
    'FuelRefer',
    'FuelCityID',
    'Oil1Price',
    'Oil2Price',
    'PropanePrice',
    'BirchPrice',
    'SprucePrice',
    'CoalPrice',
    'SteamPrice',
    'HotWaterPrice',
    'MunicipalSalesTax',
    'BoroughSalesTax'
]]
df_city.set_index('ID', inplace=True)

# Find the closest TMY3 site to each city.
# Find the Electric Utilities associated with each city.
# Determine a Natural Gas price for the city if there is 
# a natural gas utility present.
# Put all this information in the City DataFrame.
tmy_ids = []
tmy_names = []
utils = []
gas_prices = []
SELF_GEN_ID = 131   # ID number of "Self-Generation" utility
for ix, city_ser in df_city.iterrows():
    
    # get closest TMY3 site
    id, nm = closest_tmy(city_ser, df_tmy_meta)    
    tmy_ids.append(id)
    tmy_names.append(nm)
    
    # find electric utilities associated with city
    util_list = df_city_util_link.query('CityID == @ix')['UtilityID']
    df_city_utils = df_util.loc[util_list]
    elec_utils = df_city_utils.query('Type==1 and Active==1').copy()
    elec_utils.sort_values(by=['NameShort', 'IsCommercial', 'ID'], inplace=True)
    if len(elec_utils) > 0:
        utils.append(list(zip(elec_utils.Name, elec_utils.ID)))
    else:
        # If there is no Electric Utility associated with this city,
        # assign the self-generation electric utility.
        utils.append([('Self Generation', SELF_GEN_ID)])
        
    # if there is a gas utility, determine the marginal gas price
    # at a usage of 130 ccf/month, and assign that to the City.
    # This avoids the complication of working with the block rate
    # structure.
    gas_price = math.nan
    gas_utils = df_city_utils.query('Type==2 and Active==1').copy()
    # Use a residential gas utility, the smallest ID
    if len(gas_utils):
        gas_util = gas_utils.sort_values(by=['IsCommercial', 'ID']).iloc[0]
        # get the rate for a usage of 130 ccf
        for block in range(1, 6):
            block_val = gas_util['Block{}'.format(block)]
            #set_trace()
            if math.isnan(block_val) or block_val >= 130:
                gas_price = gas_util['Rate{}'.format(block)] + \
                            chg_nonnum(gas_util.FuelSurcharge, 0.0) + \
                            chg_nonnum(gas_util.PurchasedEnergyAdj, 0.0)
                break

    gas_prices.append(gas_price)

# Put all the information determined above for the cities into the
# City DataFrame as new columns.
df_city['TMYid'] = tmy_ids
df_city['TMYname'] = tmy_names
df_city['ElecUtilities'] = utils
df_city['GasPrice'] =  gas_prices

# delete out the individual block and rate columns in the utility table,
# and surcharges, as they are no longer needed.
df_util.drop(['Block{}'.format(n) for n in range(1, 6)], axis=1, inplace=True)
df_util.drop(['Rate{}'.format(n) for n in range(1, 6)], axis=1, inplace=True)
df_util.drop(['PurchasedEnergyAdj', 'FuelSurcharge'], axis=1, inplace=True)

# Also have to look to see if a city relies on another city
# for its fuel prices
for ix, cty in df_city.query('FuelRefer > 0').iterrows():
    # get the city referred to
    cty_fuel = df_city.loc[int(cty.FuelCityID)]
    # Transfer over fuel prices
    for c in df_city.columns:
        if c.endswith('Price'):
            df_city.loc[ix, c] = cty_fuel[c]

# Retrieve the Fuel information and store in a DataFrame
df_fuel = pd.read_excel(os.path.join(data_dir, 'Fuel.xlsx'), index_col='id')
df_fuel['btus'] = df_fuel.btus.astype(float)

# -------------------------------------------------------------------------------------
# These are the Pandas DataFrames and Series created from the above processing.
# They are available as module-level variables to the functions at the top of 
# this module.  A sample row, with column names is shown below.

# City Information:  df_city
# The index (not shown here) is the City ID
#
# Name                                                         Anchorage
# Latitude                                                         61.15
# Longitude                                                      -149.86
# ERHRegionID                                                          2
# WAPRegionID                                                          2
# FuelRefer                                                            0
# FuelCityID                                                         NaN
# Oil1Price                                                         3.07
# Oil2Price                                                          NaN
# PropanePrice                                                       4.5
# BirchPrice                                                         325
# SprucePrice                                                        345
# CoalPrice                                                          175
# SteamPrice                                                         NaN
# HotWaterPrice                                                      NaN
# MunicipalSalesTax                                                  NaN
# BoroughSalesTax                                                    NaN
# TMYid                                                           702730
# TMYname                                          ANCHORAGE INTL AP, AK
# ElecUtilities        [(Anchorage ML&P - Residential, 2), (Anchorage...
# GasPrice                                                          0.97

# Utility Information: df_util
# The index is the Utility ID, but also left as a column too.
#
# ID                                                              1
# Name                                Chugach Electric- Residential
# Active                                                          1
# Type                                                            1
# IsCommercial                                                    0
# ChargesRCC                                                      1
# PCE                                                             0
# CO2                                                           1.1
# CustomerChg                                                     8
# DemandCharge                                                  NaN
# NameShort                                                  Chugac
# Blocks          [(nan, 0.17713), (nan, nan), (nan, nan), (nan,...

# Miscellaneous Information (this is Pandas Series): misc_info
#
# ID                                                                      1
# LibVersion                                              2/27/2018 0:00:00  (a string)
# DiscountRate                                                         0.03
# RegSurcharge                                                       0.0032
# RegSurchargeElectric                                               0.0009
# PCEkWhLimit                                                           500
# PCEFundingPct                                                           1
# MiscNotes               Inflation factors and discount rate from 2011 ...

# Fuel Information DataFrame: df_fuel
# Index is 'id' of fuel
#
# desc         Natural Gas
# unit                 ccf
# btus              103700
# co2                  117
# effic                0.8
# price_col       GasPrice
