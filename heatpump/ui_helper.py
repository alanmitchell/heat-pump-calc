"""Functions that create lists of Dash Input and State objects,
and convert the values from the components associated with those objects
into variables suitable for passing to energy models.  Only inputs that 
are used in the Energy Model are addressed here.
"""
from dash.dependencies import Input

# shortcut for None
na = None

input_info = [
    ('city_id', 'City', ''),
    ('elec_input', 'Type of Electric Rate input', 'extra'),
    ('utility_id', 'Utility', 'null-ok,extra'),
    ('elec_rate_ez', 'Electric Rate', 'null-ok,float,extra'),
    ('pce_ez', 'PCE assistance', 'null-to-zero,float,extra'),
    ('customer_chg_ez', 'Electric Utility Customer Charge per month', 'null-to-zero,float,extra'),
    ('blk1_kwh', 'Electric Block 1 kWh limit', 'null-ok,int,extra'),
    ('blk2_kwh', 'Electric Block 2 kWh limit', 'null-ok,int,extra'),
    ('blk3_kwh', 'Electric Block 3 kWh limit', 'null-ok,int,extra'),
    ('blk4_kwh', 'Electric Block 4 kWh limit', 'null-ok,int,extra'),
    ('blk1_rate', 'Electric Block 1 rate', 'null-ok,float,extra'),
    ('blk2_rate', 'Electric Block 2 rate', 'null-ok,float,extra'),
    ('blk3_rate', 'Electric Block 3 rate', 'null-ok,float,extra'),
    ('blk4_rate', 'Electric Block 4 rate', 'null-ok,float,extra'),
    ('demand_chg_adv', 'Electric Demand Charge', 'null-to-zero,float,extra'),
    ('pce_adv', 'PCE assistance', 'null-to-zero,float,extra'),
    ('customer_chg_adv', 'Electric Customer Charge', 'null-to-zero,float,extra'),
]

def calc_input_objects():
    """Return a set of Input objects that can be used in a callback
    for the above inputs."""
    return [Input(info[0], 'value') for info in input_info]

# Default dictionary of all possible input checks and conversions.
# All checks and conversions are assumed to be not applied in the default case.
check_conversion_codes = ('null-ok', 'null-to-zero', 'float', 'int', 'extra')
check_conversion = dict(zip(check_conversion_codes, [False] * len(check_conversion_codes)))

def inputs_to_vars(input_vals):
    """This routine returns a list of input error messages and a dictionary of
    variables and associated values.  To create the dictionary of variables and
    values, conversions that are listed in the input_info list above are applied.
    """
    vars = {}
    extras = {}
    for info, val in zip(input_info, input_vals):
        cc = check_conversion.copy()
        for item in info[2].split(','):
            cc[item.strip()] = True
        if cc['extra']:
            extras[info[0]] = val
        else:
            vars[info[0]] = val
    
    return vars, extras
