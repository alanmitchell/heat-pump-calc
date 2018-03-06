"""Utility functions.
"""
import math
import numbers

def chg_nonnum(val, sub_val):
    """Changes a nan or anything that is not a number to 'sub_val'.  
    Otherwise returns val.
    """
    if isinstance(val, numbers.Number):
        if math.isnan(val):
            return sub_val
        else:
            return val
    else:
        return sub_val
