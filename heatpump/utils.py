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

def is_null(val):
    """Returns True if 'val' is None, NaN, or a blank string.
    Returns False otherwise.
    """
    if val is None:
        return True

    if isinstance(val, float) and math.isnan(val):
        return True

    if isinstance(val, str) and len(val.strip())==0:
        return True

    return False
