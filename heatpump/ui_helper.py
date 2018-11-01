"""Functions that create lists of Dash Input and State objects,
and convert the values from the components associated with those objects
into variables suitable for passing to energy models.  Only inputs that 
are used in the Energy Model are addressed here.
"""
import numbers
import numpy as np
from dash.dependencies import Input, State
from . import library as lib
from .utils import is_null

input_info = [
    ('city_id', 'City'),
    ('elec_input', 'Type of Electric Rate input', 'extra'),
    ('utility_id', 'Utility', 'null-ok,extra'),
    ('elec_rate_ez', 'Electric Rate', 'null-ok,float,greater-than-zero,extra'),
    ('pce_ez', 'PCE assistance', 'null-ok,null-to-zero,float,extra'),
    ('customer_chg_ez', 'Electric Utility Customer Charge', 'null-ok,null-to-zero,float,extra'),
    ('blk1_kwh', 'Electric Block 1 kWh limit', 'null-ok,int,greater-than-zero,extra'),
    ('blk2_kwh', 'Electric Block 2 kWh limit', 'null-ok,int,greater-than-zero,extra'),
    ('blk3_kwh', 'Electric Block 3 kWh limit', 'null-ok,int,greater-than-zero,extra'),
    ('blk4_kwh', 'Electric Block 4 kWh limit', 'null-ok,int,greater-than-zero,extra'),
    ('blk1_rate', 'Electric Block 1 rate', 'null-ok,float,extra'),
    ('blk2_rate', 'Electric Block 2 rate', 'null-ok,float,extra'),
    ('blk3_rate', 'Electric Block 3 rate', 'null-ok,float,extra'),
    ('blk4_rate', 'Electric Block 4 rate', 'null-ok,float,extra'),
    ('demand_chg_adv', 'Electric Demand Charge', 'null-ok,null-to-zero,float,extra'),
    ('pce_adv', 'PCE assistance', 'null-ok,null-to-zero,float,extra'),
    ('customer_chg_adv', 'Electric Customer Charge', 'null-ok,null-to-zero,float,extra'),
    ('no_pce_chks', 'Ignore PCE', 'extra'),
    ('co2_lbs_per_kwh', 'CO2 per kWh of extra electricity generation'),
    ('bldg_type', 'Building Type', 'extra'),
    ('commun_all_pce', 'Community Building PCE Used Up', 'extra'),
    ('bldg_floor_area', 'Building Floor Area', 'float,greater-than-zero'),
    ('garage_stall_count', 'Garage Size'),
    ('garage_heated_by_hp', 'Is Garage Heated by Heat Pump'),
    ('wall_type', 'Wall Construction Type', 'extra'),
    ('exist_heat_fuel_id', 'Heating Fuel Type'),
    ('end_uses_chks', 'End Uses using Heating Fuel', 'extra'),
    ('occupant_count', 'Number of Occupants', 'null-ok,null-to-zero,int,greater-than-zero'),
    ('exist_unit_fuel_cost', 'Heating Fuel Price', 'float,greater-than-zero'),
    ('heat_effic', 'Heating System Efficiency', 'extra'),
    ('heat_effic_slider', 'Custom-entered Heating System Efficiency', 'extra'),
    ('aux_elec', 'Auxiliary Electric Use', 'extra'),
    ('exist_fuel_use', 'Existing Heating Fuel Use', 'null-ok,float,greater-than-zero'),
    ('elec_use_jan', 'January Electric Use', 'float,greater-than-zero'),
    ('elec_use_may', 'May Electric Use', 'float,greater-than-zero'),
    ('indoor_heat_setpoint', 'Heating Thermostat'),
    ('hp_manuf_id', 'Heat Pump Manufacturer', 'extra'),    # needed to get a callback to fire
    ('hp_model_id', 'Heat Pump Model'),
    ('capital_cost', 'Installed Heat Pump Cost', 'float'),
    ('rebate_dol', 'Heat Pump Rebate', 'null-ok,null-to-zero,float'),
    ('pct_financed', '% of Heat Pump Financed'),
    ('loan_term', 'Length/Term of Loan'),
    ('loan_interest', 'Loan Interest Rate'),
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

# Make a list of Input objects and a list of State objects for each of 
# the Inputs that can affect the calculation.
input_objects = []
state_objects = []
for info in input_info:
    var_name = info[0]
    if var_name.endswith('_chks'):
        # this is a checklist component and the needed property is 'values'
        input_objects.append(Input(var_name, 'values'))
        state_objects.append(State(var_name, 'values'))
    else:
        input_objects.append(Input(var_name, 'value'))
        state_objects.append(State(var_name, 'value'))

def calc_input_objects():
    """Return a set of Input objects that can be used in a callback
    for the above inputs. 
    """
    return input_objects

def calc_state_objects():
    """Returns a list of State objects that can be used in a callback
    for the above inputs.
    """
    return state_objects

# Default dictionary of all possible input checks and conversions.
# All checks and conversions are assumed to be not applied in the default case.
check_conversion_codes = ('null-ok', 'null-to-zero', 'float', 'int', 'greater-than-zero','extra')
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

        if is_null(val):
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
            if cc['greater-than-zero']:
                if not isinstance(val, numbers.Number) or val <= 0:
                    errors.append(f'{desc} must be greater than zero.')

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

    # ------------------- Some Other Input Checks -------------------------
    if vars['loan_term'] > vars['hp_life']:
        errors.append('The Term of the Loan cannot be longer than the Life of the Heat Pump.  The Heat Pump Life can be changed in the Advanced Economic Inputs section.')
        return errors, vars, extras

    # --------------------- Electric Utility Rates ----------------------------

    # Create a utility object from the electric utility inputs.
    # To prepare for manual entry of the utility parameters, if that
    # is selected, make a real utility object from the first one listed
    # for the community and set fields to default values.
    city = lib.city_from_id(vars['city_id'])
    utility = lib.util_from_id(city.ElecUtilities[0][1])
    utility.at['Name'] = 'Custom'
    utility.at['IsCommercial'] = False
    utility.at['DemandCharge'] = np.NaN
    # Blocks, PCE, Customer Charge will be set below if this object
    # is used.

    if extras['elec_input'] == 'util':
        if is_null(extras['utility_id']):
            errors.append('You must select an Electric Utility for this City.')
            return errors, vars, extras
        else:
            utility = lib.util_from_id(extras['utility_id'])

    elif extras['elec_input'] == 'ez':
        if is_null(extras['elec_rate_ez']):
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
        for i in range(4):
            if is_null(limits[i]):
                last_ix = i
                break

        if last_ix is None:
            errors.append('The Last Electric Rate Block kWh limit must be empty.')
            return errors, vars, extras

        # Now check that all limits prior to the None are filled out
        for i in range(last_ix):
            val = limits[i]
            if is_null(val):
                errors.append(f'The Electric Rate Block {i+1} must have a kWh value.')
                return errors, vars, extras

        # Check that there are rates for all the blocks through the last
        for i in range(last_ix + 1):
            val = rates[i]
            if is_null(val):
                errors.append(f'The Electric Rate Block {i+1} must have a rate.')
                return errors, vars, extras

        # Blocks are good, so add them to the utility
        blocks = []
        for i in range(last_ix + 1):
            kwh = limits[i] if i != last_ix else np.nan
            rate = rates[i]
            blocks.append( (kwh, rate) )
        utility.at['Blocks'] = blocks
        utility.at['PCE'] = extras['pce_adv']
        utility.at['CustomerChg'] = extras['customer_chg_adv']
        utility.at['DemandCharge'] = extras['demand_chg_adv']

    vars['utility'] =  utility

    # To account for whether this building type gets PCE and to account
    # for the "ignore PCE" checkbox, set the 'pce_limit' variable.
    if 'no_pce' in extras['no_pce_chks']:
        # ignore PCE is selected
        pce_limit = 0.0
    else:
        if extras['bldg_type'] == 'res':
            pce_limit = 500.0
        elif extras['bldg_type'] == 'comm':
            # no PCE for commercial buildings
            pce_limit = 0.0
        elif extras['bldg_type'] == 'commun':
            if extras['commun_all_pce']:
                # all of the community building PCE is used up for 
                # this community
                pce_limit = 0.0
            else:
                # assume enough community building PCE left to supply the 
                # heat pump.  Thus, no limit on PCE for this building.
                pce_limit = np.inf

    # save the PCE limit variable
    vars['pce_limit'] =  pce_limit

    # -------------- Other Variables needing Processing --------------------

    # Wall Type translates to Insulation Level
    wall_to_insul = {'2x4': 1, '2x6': 2, 'better': 3}
    vars['insul_level'] = wall_to_insul[extras['wall_type']]

    # Possible manual entry of heating efficiency
    if extras['heat_effic'] == 'manual':
        vars['exist_heat_effic'] = extras['heat_effic_slider'] / 100.
    else:
        vars['exist_heat_effic'] = extras['heat_effic'] / 100.

    # Auxiliary Electricity Use of Heating System, kWh / MMBtu of heat 
    # delivered.
    aux_to_kwh = {'no-fan': 0.0, 'boiler': 4.0, 'toyo': 3.0, 
                    'furnace-effic': 6.25, 'furnace-std': 12.5}
    vars['exist_kwh_per_mmbtu'] =  aux_to_kwh[extras['aux_elec']]

    # Other End Uses using Heating Fuel
    vars['includes_dhw'] = 'dhw' in extras['end_uses_chks']
    vars['includes_dryer'] = 'drying' in extras['end_uses_chks']
    vars['includes_cooking'] = 'cooking' in extras['end_uses_chks']

    return errors, vars, extras
