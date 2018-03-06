"""Provides a class to calculate a total monthly electric utility cost
given a block rate structure, possibly including PCE. 
"""
import math

def chg_null(val, null_val):
    """Changes a nan or a None to 'null_val'.  Otherwise returns val.
    """
    if math.isnan(val) or (val is None):
        return null_val
    else:
        return val

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
        reg_surchg_add=0.0,  # $/kWh additive regulatory surcharge
        reg_surchg_mult=1.0, # multiplicative regulatory surcharge
        ):
        """Constructor parameters:
        blocks:            list of (block_kwh, block_rate) where block_kwh is max kWh for block, block_rate is $/kWh.
                               Rates must include all fuel and purchased power surcharges
        pce:               PCE rate in $/kWh; 0 if not available
        pce_limit:         maximum number kWh that PCE can apply to. None or nan if no limit.
        demand_charge:     $/kW for peak demand
        customer_charge:   Fixed charge each month in $
        reg_surchg_add:    Additive Regulatory Surcharge is $/kWh
        reg_surchg_mult:   Multiplicative Regulatory Surcharge (1.0 is no charge)
        """
        # save some of the variables for use in other methods
        self.demand_charge =  demand_charge
        self.customer_charge = customer_charge
        self.reg_surchg_mult = reg_surchg_mult

        # Make a set of blocks that:
        #   * have the quantity of kWh in the block instead of the block upper limit kWh
        #   * include a block to accomodate a PCE limit
        #   * include the regulatory surcharges

        # Convert PCE limit to infinite if no limit
        pce_limit = chg_null(pce_limit, math.inf)

        # make sure PCE adjustment is 0 if the PCE limit is 0 or less
        pce_adj = pce if pce_limit > 0.0 else 0.0
        pce_block_added = (pce_adj==0.0)     # don't need add a PCE block if no PCE.

        done = False
        temp_blocks = []
        for max_kwh, rate in blocks:
            b_kwh = chg_null(max_kwh, math.inf)
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
        
        # make the final blocks including the PCE adjustment and the 
        # regulatory surcharges
        self.__blocks = []    # final block list
        for max_kwh, rate in temp_blocks:
            if max_kwh <= pce_limit:
                rate -= pce_adj
            rate = (rate + reg_surchg_add) * reg_surchg_mult
            self.__blocks.append((max_kwh, rate))

