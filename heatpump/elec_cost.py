"""Provides a class to calculate a total monthly electric utility cost
given a block rate structure, possibly including PCE. 
"""
from math import nan, isnan, inf
from . import library as lib
from .utils import chg_nonnum

class ElecCostCalc:
    """Class to calculate monthly electric cost given a block rate structure possibly including
    PCE.
    """

    def __init__(
        self,
        utility, 
        sales_tax=0.0,      
        pce_limit=750.0,
        ):
        """Constructor parameters:
        utility:            The electric utility object from the library module.
        sales_tax:          sales tax to apply to total electric bill.
        pce_limit:          maximum number kWh that PCE can apply to. 
                                use math.nan or math.inf to indicate no limit.
        """
        # save some of the variables for use in other methods
        # add Sales Tax to any rate elements
        self.utility = utility
        self.sales_tax = sales_tax
        
        # Make a set of blocks that:
        #   * have the quantity of kWh in the block instead of the block upper limit kWh
        #   * include a block to accomodate a PCE limit
        #   * account for the effects of PCE

        # Convert PCE limit to infinite if no limit
        pce_limit = chg_nonnum(pce_limit, inf)

        if pce_limit > 0:
            # get the correct PCE rate and convert anything not a number to 0.
            pce_adj = chg_nonnum(self.utility.PCE, 0.0)
        else:
            pce_adj = 0.0

        # Flag to indicate whether a PCE block has been added.  If PCE is zero
        # no need to add a block.        
        pce_block_added = (pce_adj==0.0)  

        # Make a new set of blocks that includes the PCE limit as a new block
        # and the set is only as long as it needs to be.
        selected_blocks = self.utility.Blocks
        done = False
        temp_blocks = []
        for max_kwh, rate in selected_blocks:
            b_kwh = chg_nonnum(max_kwh, inf)
            done = (b_kwh == inf)

            # Determine whether it is time to insert the PCE block or not.
            # Test is whether block quantity exceeds the PCE limit.
            if not pce_block_added and (b_kwh > pce_limit):
                # Need to insert the PCE block now.
                temp_blocks.append( (pce_limit, rate) )
                pce_block_added = True          # PCE block has now been added.

            # address the case where the PCE limit matches the upper block
            if pce_limit == b_kwh:
                pce_block_added = True

            # add the block
            temp_blocks.append( (b_kwh, rate))

            if done:
                break

        # Include the PCE adjustment, and sales tax.
        # Also, convert the block quantities so that they are the quantity of 
        # kWh in the block instead of the upper limit of the block.
        prev_upper = 0.0
        self._blocks = []    # final block list
        for max_kwh, rate in temp_blocks:
            if max_kwh <= pce_limit:
                rate -= pce_adj
            rate *= (1. + sales_tax)
            self._blocks.append( (max_kwh - prev_upper, rate) )
            prev_upper = max_kwh

    def monthly_cost(self, kwh_energy, kw_demand=0.0):
        """Returns the total electric cost for a month, given energy usage of
        'kwh_energy' and peak demand of 'kw_demand'.
        """
        # customer charge
        cost = chg_nonnum(self.utility.CustomerChg, 0.0) * (1. + self.sales_tax)

        # demand charge
        cost += kw_demand * chg_nonnum(self.utility.DemandCharge, 0.0) * (1. + self.sales_tax)

        remaining_kwh = kwh_energy
        for b_kwh, b_rate in self._blocks:
            kwh_in_block = min(remaining_kwh, b_kwh)
            cost += kwh_in_block * b_rate
            remaining_kwh -= kwh_in_block
            if remaining_kwh < 0.1:         # 0.1 kWh in case of rounding issues
                break
        
        return cost

    def final_blocks(self):
        """Debug method to return underlying rate blocks
        """
        return self._blocks