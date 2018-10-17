"""Functions that create lists of Dash Input and State objects,
and convert the values from the components associated with those objects
into variables suitable for passing to energy models.  Only inputs that 
are used in the Energy Model are addressed here.
"""
from dash.dependencies import Input

input_info = [
    ('city_id', 'City', ''),
    ('elec_input', 'Type of Electric Rate input', 'extra'),
    ('utility_id', 'Utility', 'null-ok,extra'),
    ('elec_rate_ez', 'Electric Rate', 'null-ok,float,extra'),
    ('pce_ez', 'PCE assistance', 'null-ok,null-to-zero,float,extra'),
    ('customer_chg_ez', 'Electric Utility Customer Charge', 'null-ok,null-to-zero,float,extra'),
    ('blk1_kwh', 'Electric Block 1 kWh limit', 'null-ok,int,extra'),
    ('blk2_kwh', 'Electric Block 2 kWh limit', 'null-ok,int,extra'),
    ('blk3_kwh', 'Electric Block 3 kWh limit', 'null-ok,int,extra'),
    ('blk4_kwh', 'Electric Block 4 kWh limit', 'null-ok,int,extra'),
    ('blk1_rate', 'Electric Block 1 rate', 'null-ok,float,extra'),
    ('blk2_rate', 'Electric Block 2 rate', 'null-ok,float,extra'),
    ('blk3_rate', 'Electric Block 3 rate', 'null-ok,float,extra'),
    ('blk4_rate', 'Electric Block 4 rate', 'null-ok,float,extra'),
    ('demand_chg_adv', 'Electric Demand Charge', 'null-ok,null-to-zero,float,extra'),
    ('pce_adv', 'PCE assistance', 'null-ok,null-to-zero,float,extra'),
    ('customer_chg_adv', 'Electric Customer Charge', 'null-ok,null-to-zero,float,extra'),
    ('co2_lbs_per_kwh', 'CO2 per kWh of extra electricity generation'),
    ('bldg_type', 'Building Type', 'extra'),
    ('commun_all_pce', 'Community Building PCE Used Up', 'extra'),
    ('bldg_floor_area', 'Building Floor Area', 'float'),
    ('garage_stall_count', 'Garage Size'),
    ('wall_type', 'Wall Construction Type', 'extra'),
    ('exist_heat_fuel_id', 'Heating Fuel Type'),
    ('end_uses', 'End Uses using Heating Fuel', 'extra'),
    ('exist_unit_fuel_cost', 'Heating Fuel Price', 'float'),
    ('exist_heat_effic', 'Heating System Efficiency'),
    ('aux_elec', 'Auxiliary Electric Use', 'extra'),
    ('exist_fuel_use', 'Existing Heating Fuel Use', 'null-ok,float'),
    ('elec_use_jan', 'January Electric Use', 'float'),
    ('elec_use_may', 'May Electric Use', 'float'),
    ('indoor_heat_setpoint', 'Heating Thermostat'),
    ('hp_model_id', 'Heat Pump Model'),
    ('capital_cost', 'Installed Heat Pump Cost', 'float'),
    ('rebate_dol', 'Heat Pump Rebate', 'float'),
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
    # Separate the variables that are the final variables that are used in the
    # calculation, 'vars', from those that are secondary and will be used to
    # create main variables, 'extras'
    vars = {}
    extras = {}

    # Start a list of error messages
    errors = []

    # Make the dictionaries of main variables and extra variables, doing the
    # requested checks and conversions.
    for info, val in zip(input_info, input_vals):

        # The third info item may or may not be present so use a wildcard
        # item in the tuple unpacking.
        var, desc, *other = info

        # Start assuming no checks and conversions are present and then
        # override by those present in the third element of the info tuple.
        cc = check_conversion.copy()  # all False to start with.
        if len(other):
            for item in other[0].split(','):
                cc[item.strip()] = True

        if val is None:
            if cc['null-ok']:
                # Only other check / conversion is null to zero if the value is
                # None
                if cc['null-to-zero']:
                    val = 0
            else:
                errors.append(f'The {desc} must be entered.')
        else:
            if cc['float']:
                try:
                    # remove any commas before converting.
                    val = float(val.replace(',', ''))
                except:
                    errors.append(f'{desc} must be a number.')
            elif cc['int']:
                try:
                    val = int(val)
                except:
                    errors.append(f'{desc} must be an integer number.')

        if cc['extra']:
            extras[var] = val
        else:
            vars[var] = val
    
    return errors, vars, extras
