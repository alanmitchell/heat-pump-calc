"""Provides a class to model the impact of a heat pump on
energy use and cost.
"""
from os.path import dirname, realpath, join
import pandas as pd

this_dir = dirname(realpath(__file__))
data_dir = join(this_dir, 'data')

class HP_model:

    def __init__(self):
        self.__df_monthly = pd.read_excel(join(data_dir, 'sample_monthly.xlsx'), index_col='month')
        self.fuel_type = 3
    
    def monthly_results(self):
        """Returns a Pandas DataFrame of monthly results.
        """
        return self.__df_monthly.copy()

    def annual_results(self):
        """Returns a Pandas Series of annual results.
        """
        ann = self.__df_monthly.sum()
        # need to fix the COP annual entry, which is not a simple sum
        # of the monthly values.
        hp_load = (self.__df_monthly.cop * self.__df_monthly.elec_chg_kwh).sum()
        ann_cop = hp_load / ann.elec_chg_kwh
        ann['cop'] = ann_cop
        return ann
