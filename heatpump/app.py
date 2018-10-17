"""
Heat Pump Calculator Dash Application.
Requires version 0.23 or later of Dash.
"""
from textwrap import dedent
from pprint import pformat

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from .components import LabeledInput, LabeledSlider, LabeledSection, \
    LabeledDropdown, LabeledRadioItems, LabeledChecklist
import numpy as np	
from . import library as lib
from . import ui_helper

app = dash.Dash(__name__)
server = app.server             # this is the underlying Flask app

# This is needed to assign callbacks prior to layout being loaded, which
# is done in the LabeledSlider() component.
app.config.supress_callback_exceptions = True

# Overriding the index template allows you to change the title of the
# application and load external resources.
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Heat Pump Calculator</title>
        {%favicon%}
        {%css%}
        <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.2.0/css/all.css" integrity="sha384-hWVjflwFxL6sNzntih27bfxkr27PmbbK/iSvJ+a4+0owXq79v+lsFkW54bOGbiDQ" crossorigin="anonymous">
        <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Open+Sans|Roboto">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
        </footer>
    </body>
</html>
'''

# -------------------------------------- DEFINITIONS -------------------------------------- 
def make_options(option_list):
    """Converts a list of two-tuples: (label, value) into a list
    of dictionaries suitable for use in Dropdown and RadioItems
    components.
    """
    return [{'label': lbl, 'value': val} for lbl, val in option_list]

YES_NO = (
    ('Yes', True),
    ('No', False)
)

ELEC_INPUT_METHOD = (
    ('Select Utility Rate Schedule', 'util'),
    ('Manual Entry', 'ez'),
    ('Manual Entry (Advanced)', 'adv'),
)

BLDG_TYPE = (
    ('Residential', 'res'), 
    ('Commercial Building', 'comm'),
    ('Community Building', 'commun'),
)

GARAGE_SIZE = (
    ('No Garage', 0),
    ('1-Car', 1),
    ('2-Car', 2),
    ('3-Car', 3),
    ('4-Car', 4)
)

WALL_TYPE = (
    ('2x4', '2x4'),
    ('2x6', '2x6'),
    ('Better than 2x6', 'better'),
)

END_USES = (
    ('Domestic Water Heater', 'dhw'),
    ('Clothes Dryer', 'drying'),
    ('Range or Oven', 'cooking')
)

AUX_ELEC_TYPE = (
    ('No Fans/Pumps (e.g. wood stove)', 'no-fan'),
    ('Hydronic (boiler)', 'boiler'),
    ('Fan-assisted Space Heater (e.g. Toyostove)', 'toyo'),
    ('Forced Air Furnace', 'furnace'),
)

HP_ZONES = (
    ('Single Zone', 1),
    ('Multi Zone: 2 zones installed', 2),
    ('Multi Zone: 3 zones installed', 3),
    ('Multi Zone: 4 zones installed', 4),
)

# -------------------------------------- LAYOUT ---------------------------------------------

app.layout = html.Div(className='container', children=[
    
    html.H1('Alaska Mini-Split Heat Pump Calculator'),
    html.H2('------- UNDER CONSTRUCTION - Not Usable -------'),
    html.P('Explanation here of what the Calculator does. Credits and logos of sponsoring organizations.'),

    LabeledSection('General', [
        LabeledInput('Building Name', 'bldg_name', size=50),
        html.P('Enter in any Notes you want to be shown when you print this page.'),
        html.Textarea(style={'width': '100%'}),
    ]),

    LabeledSection('Location Info', [

        LabeledDropdown('City where Building is Located:', 'city_id',
		options=[{'label': lbl, 'value': i} for lbl, i in lib.cities()]),
        
        LabeledRadioItems('Input method:', 'elec_input',
                          'Choose "Select Utility Rate Schedule" if you would like to select a utility based on your location. Select "Manual Entry" if you would like to manually enter utility and PCE rates. Finally, select "Manual Entry (Advanced)" if you would like to enter block rates. * A copy of your utility bill will be necessary for both manual entry options.',
                          options=make_options(ELEC_INPUT_METHOD), value='util'),
        html.Div([
            LabeledDropdown('Select your Utility and Rate Schedule','utility_id', options=[],placeholder='Select Utility Company'),
            ],id='div-schedule', style={'display': 'none'}),

        html.Div([html.Table(
            [
                html.Tr( [html.Td(html.Label('Electric Rate:')), html.Td(['$ ', dcc.Input(id='elec_rate_ez', style={'maxWidth': 100}), ' /kWh'])] ),
                html.Tr( [html.Td(html.Label('PCE Rate:')), html.Td(['$ ', dcc.Input(id='pce_ez', style={'maxWidth': 100}), ' /kWh'])] ),
                html.Tr( [html.Td(html.Label('Customer Charge:')), html.Td(['$ ', dcc.Input(id='customer_chg_ez', style={'maxWidth': 100}), ' /month'])] ),                    
            ]
        ),],id='div-man-ez', style={'display': 'none'}),
        
        html.Div([
                html.Label('Enter block rates:'),
                html.Table([
                    html.Tr( [html.Th("Start kWh"), html.Th("End kWh"), html.Th("Rate, $/kWh")] ),
                    html.Tr( [html.Td(html.P("1 -")), html.Td([dcc.Input(id='blk1_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk1_rate', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk2_min')), html.Td([dcc.Input(id='blk2_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk2_rate', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk3_min')), html.Td([dcc.Input(id='blk3_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk3_rate', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk4_min')), html.Td([dcc.Input(id='blk4_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk4_rate', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td('Demand Charge:', colSpan='2'), html.Td(['$ ', dcc.Input(id='demand_chg_adv', type='text', style={'maxWidth': 100}), ' /kW/mo'])] ),
                    html.Tr( [html.Td('PCE in $/kWh', colSpan='2'), html.Td(['$ ', dcc.Input(id='pce_adv', type='text', style={'maxWidth': 100}), ' /kWh'])] ),              
                    html.Tr( [html.Td('Customer Charge in $/month', colSpan='2'), html.Td(['$ ', dcc.Input(id='customer_chg_adv', type='text', style={'maxWidth': 100}), ' /mo'])] ),
                    ])
            ], id='div-man-adv', style={'display': 'none'}),
            html.P('.'),
            
            LabeledSlider(app, 'Pounds of CO2 released per kWh of additional electricity generation:', 'co2_lbs_per_kwh', 
                0, 3.3, 'pounds/kWh',
                help_text='This is used to determine how much CO2 is released due to the electricity consumed by the heat pump.  Pick the type of generation that will be used to produce more electricity in your community.',
                max_width = 800,
                marks = {0: 'Renewables/Wood', 1.1: 'Natural Gas', 1.7: 'Lg Diesel', 2: 'Sm Diesel', 2.9: 'Coal' },
                step=0.1, value= 1.7,
                ),
    ]),

    LabeledSection('Building Info', [
        LabeledRadioItems('Type of Building:', 'bldg_type',
                options=make_options(BLDG_TYPE), value='res'),
        LabeledRadioItems('Does the Community typically use all of its Community Building PCE allotment?',
                'commun_all_pce', 
                'Select Yes if, in most months, all of the Community Building PCE is used up by the community.  If so, there will be no extra PCE is available for the heat pump kWh.',
                options=make_options(YES_NO), value=True,
                labelStyle={'display': 'inline-block'}),
        LabeledInput('Building Floor Area, excluding garage (square feet):', 'bldg_floor_area', 
                units='ft2', size=6),
        LabeledRadioItems('Size of Garage:', 'garage_stall_count', 
                options=make_options(GARAGE_SIZE), value=0),
        LabeledRadioItems('Will the Heat Pump be used to Heat the Garage?',
                'garage_heated_by_hp',
                options=make_options(YES_NO), value=False,
                labelStyle={'display': 'inline-block'}),
        LabeledRadioItems('Wall Construction:', 'wall_type', 
                options=make_options(WALL_TYPE), value = '2x6'),
        LabeledDropdown('Select existing Space Heating Fuel type:', 'exist_heat_fuel_id',
                options=[{'label': lbl, 'value': i} for lbl, i in lib.fuels()]),
        LabeledChecklist('Besides Space Heating, what other Appliances use this Fuel?', 'end_uses_chks',
                         options=make_options(END_USES), values=[]),
        LabeledInput('Number of Occupants in Building using Above End Uses:', 'occupant_count',
                'people', value=3),
        LabeledInput('Fuel Price Per Unit:', 'exist_unit_fuel_cost'),     
        LabeledRadioItems('Efficiency of Existing Heating System:','exist_heat_effic', max_width=500),
        LabeledRadioItems('Auxiliary electricity use (fans/pumps/controls) from existing heating system:', 'aux_elec', 
                options=make_options(AUX_ELEC_TYPE), value='toyo',
                help_text='Choose the type of heating system you currently have installed. This input will be used to estimate the electricity use by that system.',
                ),
		LabeledInput('Annual Fuel Use for building including heating and any other uses identified above (Optional, but very helpful!):', 'exist_fuel_use', 
                help_text='This value is optional and may be left blank. If left blank, size and construction will be used to estimate existing fuel use. Please use physical units ex: gallons, CCF, etc.'),
        LabeledInput('Whole Building Electricity Use (without heat pump) in January:', 'elec_use_jan', 'kWh', 
                help_text='This defaults to the value found for this City, please don\'t adjust unless you have your utility bill with actual numbers.'),
        LabeledInput('Whole Building Electricity Use (without heat pump) in May:', 'elec_use_may', 'kWh', 
                help_text='This defaults to the value found for this City, please don\'t adjust unless you have your utility bill with actual numbers.'),
        html.Br(),
        LabeledSlider(app, 'Heating Temperature Setpoint:', 'indoor_heat_setpoint',
                      60, 80, '°F',
                      mark_gap=5, step=1, value=71),
    ]),
    LabeledSection('Heat Pump Info', [
        
        LabeledRadioItems('Type of Heat Pump: Single- or Multi-zone', 'hp_zones',
                          'Select the number of Indoor Units (heads) installed on the Heat Pump.',
                          options=make_options(HP_ZONES), value=1),
        LabeledChecklist('Show Most Efficient Units Only?', 'efficient_only',
                         options=[{'label': 'Efficient Only', 'value': 'efficient'}],
                         values=['efficient']),
        LabeledDropdown('Heat Pump Manufacturer', 'hp_manuf_id',
                        options=[],
                        max_width=300,
                        placeholder='Select Heat Pump Manufacturer'),   
        LabeledDropdown('Heat Pump Model', 'hp_model_id',
                        options=[],
                        max_width=1000,   # wide as possible
                        placeholder='Select Heat Pump Model',
                        style={'fontSize': 14}),
        LabeledInput('Installed Cost of Heat Pump, $', 'capital_cost', '$', 
                     'Include all equipment and labor costs.', value=4500),
        LabeledInput('Rebates Received for Heat Pump, $', 'rebate_dol', '$',
                     'Enter the dollar amount of any rebates received for installation of the heat pump.',
                     value=0),
        LabeledSlider(app, '% of Heat Pump Purchase Financed with a Loan', 'pct_financed', 
                      0, 100, '%', 
                      'Select 0 if the purchased is not financed.',
                      mark_gap=10, max_width=700,
                      step=1, value=0),
        html.Div([
            LabeledSlider(app, 'Length (Term) of Loan', 'loan_term',
                        3, 14, 'years',
                        'Numbers of Years to pay off Loan.',
                        mark_gap=1, max_width=700,
                        step=1, value=10),
            LabeledSlider(app, 'Loan Interest Rate', 'loan_interest',
                        0, 12, '%',
                        'Numbers of Years to pay off Loan.',
                        mark_gap=1, max_width=700,
                        step=0.1, value=4),
        ], id='div-loan', style={'display': 'none'}),
        LabeledRadioItems('Are the Heat Pump Indoor Units mounted 6 feet or higher on the wall?',
                'indoor_high_mount', 
                'If most or all of the heat-delivering Indoor Units are mounted high on the wall, check this box.  High mounting of Indoor Units slightly decreases the efficiency of the heat pump.',
                options=make_options(YES_NO), value=True,
                labelStyle={'display': 'inline-block'}),
        LabeledSlider(app, 'Heat Pump is Turned Off below this Outdoor Temperature:', 
                    'low_temp_cutoff', 
                    -20, 20, '°F', 
                    'Please enter the lowest outdoor temperature at which the heat pump will continue to operate. The turn off of the heat pump can either be due to technical limits of the heat pump, or due to the homeowner choosing to not run the heat pump in cold temperatures due to poor efficiency.', 
                    mark_gap=5, step=1, value=5),
    ]),

    LabeledSection('Economic Inputs', [

        html.Details(style={'maxWidth': 550}, children=[
            html.Summary('Click Here to see Advanced Economic Inputs'),
            html.Div(style={'marginTop': '3rem'}, children=[
                LabeledSlider(app, 'Sales Tax:', 'sales_tax',
                            0, 10, '%',
                            'Enter your city/state sales tax.  This will be applied to the heat pump installed cost and to electricity and fuel prices',
                            mark_gap=1, step=0.1, value=0),                            
                LabeledSlider(app, 'General Inflation Rate:', 'inflation_rate',
                            0, 6, '%',
                            'The default is the inflation rate used by the U.S. Department of Energy. Change this only in special circumstances.',
                            mark_gap=1, step=0.1, value=2),
                LabeledSlider(app, 'Heating Fuel Price Inflation Rate:', 'fuel_esc_rate',
                            0, 8, '%',
                            'This is the predicted annual increase in the price of the chosen heating fuel, based on U.S. Department of Energy estimates.',
                            mark_gap=1, step=0.1, value=4),    
                LabeledSlider(app, 'Electricity Price Inflation Rate:', 'elec_esc_rate',
                            0, 8, '%',
                            'This is the predicted annual increase in the price of electricity in this location, based on U.S. Department of Energy estimates.',
                            mark_gap=1, step=0.1, value=2),        
                LabeledSlider(app, 'Discount Rate:', 'discount_rate',
                            3, 12, '%',
                            'Enter the Economic Discount Rate, i.e the threshhold rate-of-return for this type of investment.  This rate is a nominal rate *not* adjusted for inflation.',
                            mark_gap=1, step=0.1, value=5),
                LabeledSlider(app, 'Life of Heat Pump:', 'hp_life',
                            5, 25, 'years',
                            'This should be set to 14 years unless there is evidence that a particular model will last shorter or longer than most heat pumps.',
                            mark_gap=2, step=1, value=14),    
                LabeledInput('Annual increase in heating system O&M Cost:', 'op_cost_chg', 
                            '$/year', 
                            'Enter a positive value if the cost of maintaining the heating systems with the heat pump is higher than the cost of maintaining the previous system.'),
            ])
        ])

    ]),

    LabeledSection('Results', [
        html.H3('Results go Here!'), 
        dcc.Markdown('Key Inputs.', id='key-inputs')
    ]),

    html.Hr(),

    html.P('Some sort of Footer goes here.'),

])

# -------------------------------------- CALLBACKS ---------------------------------------------

@app.callback(Output('utility_id', 'options'),
    [Input('city_id', 'value')])
def find_util(city_id):
    if city_id is None:
        return []
    utils = lib.city_from_id(city_id).ElecUtilities
    return [{'label': util_name, 'value': util_id} for util_name, util_id in utils]
    
@app.callback(Output('div-schedule', 'style'), 
    [Input('elec_input','value')])
def electricalinputs(elec_input):
    if elec_input == 'util':
        return {'display': 'block'}
    else:
        return {'display': 'none'}
    
@app.callback(Output('div-man-ez', 'style'), 
    [Input('elec_input','value')])
def electricalinputs_ez(elec_input):
    if elec_input == 'ez':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('div-man-adv', 'style'), 
    [Input('elec_input','value')])
def electricalinputs_adv(elec_input):
    if elec_input == 'adv':
        return {'display': 'block'}
    else:
        return {'display': 'none'}   
        
@app.callback(Output('blk2_min','children'), [Input('blk1_kwh','value')])
def setblockkwh1(blk0_kwh):
    try:
        return f'{int(blk0_kwh) + 1} -'
    except:
        return None

@app.callback(Output('blk3_min','children'), [Input('blk2_kwh','value')])
def setblockkwh2(blk1_kwh):
    try:
        return f'{int(blk1_kwh) + 1} -'
    except:
        return None

@app.callback(Output('blk4_min','children'), [Input('blk3_kwh','value')])
def setblockkwh3(blk2_kwh):
    try:
        return f'{int(blk2_kwh) + 1} -'
    except:
        return None

@app.callback(Output('exist_unit_fuel_cost', 'value'),
    [Input('exist_heat_fuel_id', 'value'), Input('city_id','value')])
def find_fuel_price(fuel_id, city_id):
    if fuel_id is None or city_id is None:
        return None
    the_fuel = lib.fuel_from_id(fuel_id)
    price_col = the_fuel['price_col']
    the_city = lib.city_from_id(city_id)
    price = np.nan_to_num(the_city[price_col])
    price = np.round(price, 2)
    
    return price 

@app.callback(Output('exist_heat_effic','options'), [Input('exist_heat_fuel_id', 'value')])
def effic_choices(fuel_id):
    if fuel_id is None:
        return []
    fu = lib.fuel_from_id(fuel_id)
    return [{'label': lbl, 'value': val} for lbl, val in fu.effic_choices]

@app.callback(Output('exist_heat_effic','value'), [Input('exist_heat_effic','options')])
def options(ht_eff):
    if len(ht_eff)>2:
        return ht_eff[1]['value']
    elif len(ht_eff)>0:
        return ht_eff[0]['value']
    else:
        return None

@app.callback(Output('units-exist_fuel_use', 'children'),[Input('exist_heat_fuel_id','value')])
def update_use_units(fuel_id):
    if fuel_id is None:
        return None
    fuel = lib.fuel_from_id(fuel_id)
    return fuel.unit  

@app.callback(Output('units-exist_unit_fuel_cost', 'children'),[Input('exist_heat_fuel_id','value')])
def update_price_units(fuel_id):
    if fuel_id is None:
        return None
    fuel = lib.fuel_from_id(fuel_id)
    return f'$ / {fuel.unit}'
    
@app.callback(Output('elec_use_jan','value'),[Input('city_id','value')])
def whole_bldg_jan(city_id):
    if city_id is None:
        return None
    jan_elec = lib.city_from_id(city_id).avg_elec_usage[0]
    jan_elec = np.round(jan_elec, 0)
    return jan_elec
    
@app.callback(Output('elec_use_may','value'),[Input('city_id','value')])
def whole_bldg_may(city_id):
    if city_id is None:
        return None
    may_elec = lib.city_from_id(city_id).avg_elec_usage[4]
    may_elec = np.round(may_elec, 0)
    return may_elec

@app.callback(Output('div-garage_heated_by_hp', 'style'), 
    [Input('garage_stall_count','value')])
def garage_heated(stalls):
    if stalls > 0:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('hp_manuf_id', 'options'), 
    [Input('hp_zones', 'value'), Input('efficient_only', 'values')])
def hp_brands(zones, effic_check_list):
    zone_type = 'Single' if zones==1 else 'Multi'
    manuf_list = lib.heat_pump_manufacturers(zone_type, 'efficient' in effic_check_list)
    return [{'label': brand, 'value': brand} for brand in manuf_list]

@app.callback(Output('hp_model_id', 'options'), 
              [Input('hp_manuf_id', 'value'), Input('hp_zones', 'value'), Input('efficient_only', 'values')])
def hp_models(manuf, zones, effic_check_list):
    zone_type = 'Single' if zones==1 else 'Multi'
    model_list = lib.heat_pump_models(manuf, zone_type, 'efficient' in effic_check_list)
    return [{'label': lbl, 'value': id} for lbl, id in model_list]

@app.callback(Output('div-loan', 'style'), 
    [Input('pct_financed','value')])
def loan_inputs(pct_financed):
    if pct_financed > 0:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('key-inputs', 'children'), 
    ui_helper.calc_input_objects())
def show_key_inputs(*args):
    errors, vars, extra_vars = ui_helper.inputs_to_vars(args)

    return dedent(f'''
    ```
    Errors:
    {pformat(errors)}

    Variables:
    {pformat(vars)}

    Extra Variables:
    {pformat(extra_vars)}
    ```
    ''')

# -------------------------------------- MAIN ---------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)   # use on Windows computer
