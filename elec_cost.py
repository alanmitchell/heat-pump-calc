"""Provides a class to calculate a total monthly electric utility cost
given a block rate structure, possibly including PCE. 
"""
import math
from utils import chg_nonnum

class ElecCostCalc:
    """Class to calculate monthly electric cost given a block rate structure possibly including
    PCE.
    """

    def __init__(
        self,
        blocks,  # list of (block_kwh, block_rate) where block_kwh is max kWh for block, block_rate is $/kWh
        pce=0.0,             # PCE rate in $/kWh; 0 if not available
        pce_limit=500.0,     # maximum number kWh that PCE can apply to. None or nan if no limit.
        demand_charge=0.0,   # $/kW for peak demand
        customer_charge=0.0, # Fixed charge each month in $
        reg_surchg=0.0,      # $/kWh additive regulatory surcharge
        sales_tax=0.0,       # sales tax, as a decimal fraction applied to electric utility costs.
        ):
        """Constructor parameters:
        blocks:            list of (block_kwh, block_rate) where block_kwh is max kWh for block, block_rate is $/kWh.
                               Rates must include all fuel and purchased power surcharges
        pce:               PCE rate in $/kWh; 0 if not available
        pce_limit:         maximum number kWh that PCE can apply to. None or nan if no limit.
        demand_charge:     $/kW for peak demand
        customer_charge:   Fixed charge each month in $
        reg_surchg:        Additive Regulatory Surcharge is $/kWh
        """
        # save some of the variables for use in other methods, but include sales tax
        self.demand_charge =  demand_charge * (1. + sales_tax)
        self.customer_charge = customer_charge * (1. + sales_tax)

        # Make a set of blocks that:
        #   * have the quantity of kWh in the block instead of the block upper limit kWh
        #   * include a block to accomodate a PCE limit
        #   * include the regulatory surcharges

        # Convert PCE limit to infinite if no limit
        pce_limit = chg_nonnum(pce_limit, math.inf)

        # make sure PCE adjustment is 0 if the PCE limit is 0 or less
        pce_adj = pce if pce_limit > 0.0 else 0.0
        pce_block_added = (pce_adj==0.0)     # don't need add a PCE block if no PCE.

        done = False
        temp_blocks = []
        for max_kwh, rate in blocks:
            b_kwh = chg_nonnum(max_kwh, math.inf)
            done = (b_kwh == math.inf)

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

        # Include the PCE adjustment, the regulatory surcharges, and sales tax.
        # Also, convert the block quantities so that they are the quantity of 
        # kWh in the block instead of the upper limit of the block.
        prev_upper = 0.0
        self.__blocks = []    # final block list
        for max_kwh, rate in temp_blocks:
            if max_kwh <= pce_limit:
                rate -= pce_adj
            rate += reg_surchg
            rate *= (1. + sales_tax)
            self.__blocks.append( (max_kwh - prev_upper, rate) )
            prev_upper = max_kwh

    def final_blocks(self):
        """Debug method to return underlying rate blocks
        """
        return self.__blocks