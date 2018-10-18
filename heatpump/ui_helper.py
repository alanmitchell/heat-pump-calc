"""Functions that create lists of Dash Input and State objects,
and convert the values from the components associated with those objects
into variables suitable for passing to energy models.  Only inputs that 
are used in the Energy Model are addressed here.
"""
import numpy as np
from dash.dependencies import Input
from . import library as lib

input_info = [
    ('city_id', 'City'),
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
    ('end_uses_chks', 'End Uses using Heating Fuel', 'extra'),
    ('exist_unit_fuel_cost', 'Heating Fuel Price', 'float'),
    ('exist_heat_effic', 'Heating System Efficiency'),
    ('aux_elec', 'Auxiliary Electric Use', 'extra'),
    ('exist_is_point_source', 'Existing Heating is One Room'),
    ('exist_fuel_use', 'Existing Heating Fuel Use', 'null-ok,float'),
    ('elec_use_jan', 'January Electric Use', 'float'),
    ('elec_use_may', 'May Electric Use', 'float'),
    ('indoor_heat_setpoint', 'Heating Thermostat'),
    ('hp_model_id', 'Heat Pump Model'),
    ('capital_cost', 'Installed Heat Pump Cost', 'float'),
    ('rebate_dol', 'Heat Pump Rebate', 'float'),
    ('pct_financed', '% of Heat Pump Financed'),
    ('loan_term', 'Length/Term of Loan'),
    ('loan_interest', 'Loan Interest Rate'),
    ('indoor_high_mount', 'High Mounting of Indoor Units'),
    ('low_temp_cutoff', 'Low Temperature Cutoff of Heat Pump'),
    ('pct_exposed_to_hp', 'Percent of Home Open to Heat Pump'),
    ('bedroom_temp_tolerance', 'Bedroom Temperature Tolerance'),
    ('doors_open_to_adjacent', 'Doors Open to Adjacent Spaces'),
    ('sales_tax', 'Sales Tax'),
    ('inflation_rate', 'Inflation Rate'),
    ('fuel_esc_rate', 'Fuel Price Escalation Rate'),
    ('elec_esc_rate', 'Electricity Price Escalation Rate'),
    ('discount_rate', 'Discount Rate'),
    ('hp_life', 'Heat Pump Life'),
    ('op_cost_chg', 'Operating Cost Change', 'null-ok,null-to-zero,float'),
]

def calc_input_objects():
    """Return a set of Input objects that can be used in a callback
    for the above inputs.  The 'value' property for each component is
    used in the callback unless the component ID ends in '_chks'; in that
    case the component is a checklist, and the 'values' property is used.
    """
    in_list = []
    for info in input_info:
        var_name = info[0]
        if var_name.endswith('_chks'):
            # this is a checklist component and the needed property is 'values'
            in_list.append(Input(var_name, 'values'))
        else:
            in_list.append(Input(var_name, 'value'))

    return in_list

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
                    if isinstance(val, str):
                        # remove any commas before converting.
                        val = val.replace(',', '')
                    val = float(val)
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

    if len(errors):
        # Because of errors, no point in going further.
        return errors, vars, extras

    # convert percentage values to fractions
    vars['discount_rate'] /= 100.
    vars['elec_esc_rate'] /= 100.
    vars['fuel_esc_rate'] /= 100.
    vars['inflation_rate'] /= 100.
    vars['loan_interest'] /= 100.
    vars['pct_financed'] /= 100.
    vars['sales_tax'] /= 100.
    vars['pct_exposed_to_hp'] /= 100.

    # Create a utility object from the electric utility inputs.
    # Start with a real utility object from the first one listed
    # for the community and set fields to default values.
    city = lib.city_from_id(vars['city_id'])
    utility = lib.util_from_id(city.ElecUtilities[0][1])
    utility.at['Name'] = 'Custom'
    utility.at['IsCommercial'] = False
    utility.at['DemandCharge'] = np.NaN
    # Blocks, PCE, Customer Charge will be set below if this object
    # is used.

    if extras['elec_input'] == 'util':
        if extras['utility_id'] is None:
            errors.append('You must select an Electric Utility for this City.')
            return errors, vars, extras
        else:
            utility = lib.util_from_id(extras['utility_id'])

    elif extras['elec_input'] == 'ez':
        if extras['elec_rate_ez'] is None:
            errors.append('You must enter an Electric Rate for this City.')
            return errors, vars, extras
        else:
            # just one block
            utility.at['Blocks'] = [(np.NaN, extras['elec_rate_ez'])]
            utility.at['PCE'] = extras['pce_ez']
            utility.at['CustomerChg'] = extras['customer_chg_ez']

    else:
        # Advanced utility rate input
        # Need to check block limits and rates to see if they are in 
        # the correct format.

        # make a list of limits and a list of block rates
        limits = [extras[f'blk{i}_kwh'] for i in range(1, 5)]
        rates = [extras[f'blk{i}_rate'] for i in range(1, 5)]

        # there must be a None at the last block
        last_ix = None
        for i in reversed(range(4)):    # look from the top down
            if limits[i] is None:
                last_ix = i
                break
                
        if last_ix is None:
            errors.append('The Last Electric Rate Block kWh limit must be empty.')
            return errors, vars, extras

    vars['utility'] =  utility

    return errors, vars, extras
