"""Functions that create lists of Dash Input and State objects,
and convert the values from the components associated with those objects
into variables suitable for passing to energy models.  Only inputs that 
are used in the Energy Model are addressed here.
"""
from dash.dependencies import Input

# shortcut for None
na = None

input_info = [
    ('city', 'city_id'),
    ('elec_input',),
    ('utility', 'utility_id'),
    ('elec_rate_ez',),
    ('pce_ez', ),
    ('customer_chg_ez', ),
    ('blk1_min', ), 
    ('blk2_min', ), 
    ('blk3_min', ), 
    ('blk0_kwh', ),
    ('blk1_kwh', ),
    ('blk2_kwh', ),
    ('blk3_kwh', ),
    ('blk0_rate', ),
    ('blk1_rate', ),
    ('blk2_rate', ),
    ('blk3_rate', ),
    ('demand_chg_adv', ),
    ('pce_adv', ),
    ('customer_chg_adv', ),
]

def calc_input_objects():
    """Return a set of Input objects that can be used in a callback
    for the above inputs."""
    ids, = list(zip(*input_info))
    return [Input(id, 'value') for id in ids]

def inputs_to_vars(input_vals):
    """Converts a tuple of values from the input_info list of components
    into a dictionaries of variables suitable for use in the energy models.
    """
    vars = {}
    extra_vars = {}
    for info, val in zip(input_info, input_vals):
        if len(info) > 1 and info[1] is not None:
            var_name = info[1]
        else:
            var_name = info[0]
        vars[var_name] = val
    
    return vars, extra_vars
