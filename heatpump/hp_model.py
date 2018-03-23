"""Provides a class to model the impact of a heat pump on
energy use and cost.
"""
from os.path import dirname, realpath, join
import pandas as pd
import numpy as np

this_dir = dirname(realpath(__file__))
data_dir = join(this_dir, 'data')

def make_pattern(esc, life):
    """Makes a numpy array of length (life + 1) containing an escalation pattern
    that starts with a 1.0 in year 1 and escalates at the rate of 'esc' per year.
    """
    pat = np.ones(life - 1) * (1 + esc)
    return np.insert(pat.cumprod(), 0, [0.0, 1.0])

class HP_model:

    def __init__(self):
        self.__df_monthly = pd.read_excel(join(data_dir, 'sample_monthly.xlsx'), index_col='month', sheet_name='with_pce')
        self.__df_monthly_no_pce = pd.read_excel(join(data_dir, 'sample_monthly.xlsx'), index_col='month', sheet_name='without_pce')
        self.fuel_type = 3
    
    def monthly_results(self, ignore_pce=False):
        """Returns a Pandas DataFrame of monthly results.
        If 'ignore_pce' is True, does not include PCE subsidy in analysis.
        """

        return self.__df_monthly_no_pce.copy() if ignore_pce else self.__df_monthly.copy()

    def annual_results(self, ignore_pce=False):
        """Returns a Pandas Series of annual results.
        If 'ignore_pce' is True, does not include PCE subsidy in analysis.
        """
        ann = self.monthly_results(ignore_pce=ignore_pce).sum()
        # need to fix the COP annual entry, which is not a simple sum
        # of the monthly values.
        hp_load = (self.__df_monthly.cop * self.__df_monthly.elec_chg_kwh).sum()
        ann_cop = hp_load / ann.elec_chg_kwh
        ann['cop'] = ann_cop
        return ann

    def cash_flow(self, ignore_pce=False):
        """Returns a Pandas DataFrame showing cash flow impacts over the
        life of the heat pump.
        If 'ignore_pce' is True, does not include PCE subsidy in analysis.
        """
        life = 14    # years of life
        ann = self.annual_results(ignore_pce=ignore_pce)
        capital = np.zeros(life+1)
        capital[0] = 4500.
        operating = 20. * make_pattern(.02, life)
        fuel_cost_savings = -ann.fuel_chg_dol * make_pattern(.04, life)
        elec_cost_increase = ann.elec_chg_dol * make_pattern(.03, life)
        cash_flow = -capital + -operating + fuel_cost_savings - elec_cost_increase
        df = pd.DataFrame(
            {'capital_cost': capital,
             'operating_cost': operating,
             'fuel_cost_savings': fuel_cost_savings,
             'elec_cost_increase': elec_cost_increase,
             'cash_flow': cash_flow
            }
        )
        df.index.name = 'year'

        return df

    def irr(self, ignore_pce=False):
        """Returns the internal rate of return of the heat pump investment.
        If 'ignore_pce' is True, does not include PCE subsidy in analysis.
        """
        df_cash = self.cash_flow(ignore_pce=ignore_pce)
        return np.irr(df_cash.cash_flow)

    def npv(self, ignore_pce=False):
        """Returns the net present value of the heat pump investment.
        If 'ignore_pce' is True, does not include PCE subsidy in analysis.
        """
        df_cash = self.cash_flow(ignore_pce=ignore_pce)
        return np.npv(0.05, df_cash.cash_flow)
