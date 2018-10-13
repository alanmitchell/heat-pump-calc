"""
Heat Pump Calculator Dash Application.
Requires version 0.23 or later of Dash.
"""
from textwrap import dedent

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from .components import LabeledInput, LabeledSlider, LabeledSection, LabeledTextInput, \
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

WALL_TYPE = (
    ('2x4', '2x4'),
    ('2x6', '2x6'),
    ('Better than 2x6', 'better'),
)

AUX_ELEC_TYPE = (
    ('No Fans/Pumps (e.g. wood stove)', 'no-fan'),
    ('Hydronic (boiler)', 'boiler'),
    ('Fan-assisted Space Heater (e.g. Toyostove)', 'toyo'),
    ('Forced Air Furnace', 'furnace'),
)  

# -------------------------------------- LAYOUT ---------------------------------------------

app.layout = html.Div(className='container', children=[
    
    html.H1('Alaska Mini-Split Heat Pump Calculator'),
    html.H2('------- UNDER CONSTRUCTION - Not Usable -------'),
    html.P('Explanation here of what the Calculator does. Credits and logos of sponsoring organizations.'),

    LabeledSection('General', [
        LabeledTextInput('Building Name', 'bldg_name', size=50),
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
            ],id='div-schedule',style={'display': 'none'}),

        html.Div([html.Table(
            [
                html.Tr( [html.Td(html.Label('Electric Rate:')), html.Td(['$ ', dcc.Input(id='elec_rate_ez',type='number', style={'maxWidth': 100}), ' /kWh'])] ),
                html.Tr( [html.Td(html.Label('PCE Rate:')), html.Td(['$ ', dcc.Input(id='pce_ez', type='number', style={'maxWidth': 100}), ' /kWh'])] ),
                html.Tr( [html.Td(html.Label('Customer Charge:')), html.Td(['$ ', dcc.Input(id='customer_chg_ez', type='number', style={'maxWidth': 100}), ' /month'])] ),                    
            ]
        ),],id='div-man-ez', style={'display': 'none'}),
        
        html.Div([html.Label('Enter block rates:'),
            html.Table(
                [
                    html.Tr( [html.Th("Start kWh"), html.Th("End kWh"), html.Th("Rate, $/kWh")] ),
                    html.Tr( [html.Td(html.P("1 -")), html.Td([dcc.Input(id='blk0_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk0_rate', type='number', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk1_min')), html.Td([dcc.Input(id='blk1_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk1_rate', type='number', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk2_min')), html.Td([dcc.Input(id='blk2_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk2_rate', type='number', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk3_min')), html.Td([dcc.Input(id='blk3_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk3_rate', type='number', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td('Demand Charge:', colSpan='2'), html.Td(['$ ', dcc.Input(id='demand_chg_adv', type='number', style={'maxWidth': 100}), ' /kW/mo'])] ),
                    html.Tr( [html.Td('PCE in $/kWh', colSpan='2'), html.Td(['$ ', dcc.Input(id='pce_adv',type='number', style={'maxWidth': 100}), ' /kWh'])] ),              
                    html.Tr( [html.Td('Customer Charge in $/month', colSpan='2'), html.Td(['$ ', dcc.Input(id='customer_chg_adv',type='number', style={'maxWidth': 100}), ' /mo'])] ),
                ]
            ),],id='div-man-adv', style={'display': 'none'}),

            html.P('.'),
            
            LabeledSlider(app, 'Pounds of CO2 per kWh of incremental electricity generation:', 'elec-co2', 
                0, 3.3, 'pounds/kWh',
                max_width = 800,
                marks = {0: 'Renewables/Wood', 1.1: 'Natural Gas', 1.7: 'Lg Diesel', 2: 'Sm Diesel', 2.9: 'Coal' },
                step=0.1, value= 1.7,
                ),
    ]),

    LabeledSection('Building Info', [
        LabeledInput('Building Floor Area, excluding garage (square feet)', 'ht_floor_area', size=6),
        LabeledRadioItems('Wall Construction', 'wall_const', 
                options=make_options(WALL_TYPE), value = '2x6'),
        LabeledDropdown('Select existing heating fuel type', 'fuel',
                options=[{'label': lbl, 'value': i} for lbl, i in lib.fuels()]),
        LabeledInput('Fuel Price Per Unit', 'fuel_price', '$'),     
        LabeledRadioItems('Efficiency of Existing Heating System','ht_eff', max_width=500),
        LabeledRadioItems('Auxiliary electricity use from existing heating system', 'aux_elec', 
                options=AUX_ELEC_TYPE, value='toyo',
                help_text='Choose the type of heating system you currently have installed. This input will be used to estimate the electricity use by that system.',
                ),
        #the item below needs to be labeledinput and assigned a number type once we figure out how to get the units tag to go where it's supposed to
		LabeledInput('(Optional) Annual space heating Fuel Use for building in physical units','sp_ht_use', help_text='This value is optional and may be left blank. If left blank, size, year built, and construction will be used to estimate existing fuel use. Please use physical units ex: gallons, CCF, etc.'),
        LabeledInput('Whole Building Electricity Use (without heat pump) in January', 'jan_elec', 'kWh', help_text='This defaults to the value found for this City, please don\'t adjust unless you have your utility bill with actual numbers.'),
        LabeledInput('Whole Building Electricity Use (without heat pump) in May', 'may_elec', 'kWh', help_text='This defaults to the value found for this City, please don\'t adjust unless you have your utility bill with actual numbers.'),
        html.Br(),
        LabeledSlider(app, 'Indoor Temperature where Heat Pump is Located', 'indoor-temp',
                      60, 80, '°F',
                      mark_gap=5, step=1, value=71),
    ]),

    LabeledSection('Heat Pump Info', [
        
        LabeledRadioItems('Type of Heat Pump: Single- or Multi-zone', 'zones',
                          'Select the number of Indoor Units (heads) installed on the Heat Pump.',
                          options= [
                              {'label': 'Single Zone', 'value': 1},
                              {'label': 'Multi Zone: 2 zones installed', 'value': 2},
                              {'label': 'Multi Zone: 3 zones installed', 'value': 3}],
                          value=1),
        
        LabeledChecklist('Show Most Efficient Units Only?', 'efficient-only',
                         options=[{'label': 'Efficient Only', 'value': 'efficient'}],
                         values=['efficient']),

        LabeledDropdown('Heat Pump Manufacturer', 'hp-manuf',
                        options=[],
                        max_width=300,
                        placeholder='Select Heat Pump Manufacturer'),   

        LabeledDropdown('Heat Pump Model', 'hp-model',
                        options=[],
                        max_width=1000,   # wide as possible
                        placeholder='Select Heat Pump Model',
                        style={'fontSize': 14}),

        LabeledInput('Installed Cost of Heat Pump', 'hp-cost', '$', 
                     'Include all equipment and labor costs.', value=4500),

        LabeledSlider(app, '% of Heat Pump Purchase Financed with a Loan', 'pct-financed', 
                      0, 100, '%', 
                      'Select 0 if the purchased is not financed.',
                      mark_gap=10, max_width=700,
                      step=5, value=0),
        LabeledInput('Term of Loan', 'loan-term', 'years',
                     'Numbers of Years to pay off Loan.', value=10),

        LabeledChecklist('Check the Box if Indoor Units are mounted 6 feet or higher on wall',
                         'indoor-unit-height',
                         'If most or all of the heat-delivering Indoor Units are mounted high on the wall, check this box.  High mounting of Indoor Units slightly decreases the efficiency of the heat pump.',
                         max_width=500,
                         options=[{'label': "Indoor Unit mounted 6' or higher", 'value': 'in_ht_6'}],
                         values=['in_ht_6']),

        LabeledChecklist('When the heat pump is operating, does it serve all areas of the building, or does another heat source serve some areas?:',
                         'serve-all-bldg',
                         'If there is another heat source for the back bedrooms, for example, do *not* check the box.',
                         max_width=700,
                         options=[{'label': "Heat Pump serves the entire Building when Operating.", 'value': 'serves_all'}],
                         values=[]),
        LabeledSlider(app, 'Minimum Operating Temperature of Heat Pump', 'min_op_temp', -20, 20, '°F', help_text='Please enter the lowest outdoor temperature at which the heat pump will continue to operate. This should be available in the unit’s documentation. The turn off of the heat pump can either be due to technical limits of the heat pump, or due to the homeowner choosing to not run the heat pump in cold temperatures due to poor efficiency.', mark_gap=5, step=1, value=5),
    ]),

    LabeledSection('Economic Inputs', [

        html.Details(style={'maxWidth': 550}, children=[
            html.Summary('Click Here to see Advanced Economic Inputs'),
            html.Div(style={'marginTop': '3rem'}, children=[
                LabeledSlider(app, 'General Inflation Rate:', 'inf-rate',
                            0, 10, '%',
                            'The default is the inflation rate used by the U.S. Department of Energy. Change this only in special circumstances.',
                            mark_gap=1, step=0.5, value=2),
                LabeledSlider(app, 'Heating Fuel Price Inflation Rate:', 'fuel-inf-rate',
                            0, 10, '%',
                            'This is the predicted annual increase in the price of the chosen heating fuel, based on U.S. Department of Energy estimates.',
                            mark_gap=1, step=0.5, value=4),    
                LabeledSlider(app, 'Electricity Price Inflation Rate:', 'elec-inf-rate',
                            0, 10, '%',
                            'This is the predicted annual increase in the price of electricity in this location, based on U.S. Department of Energy estimates.',
                            mark_gap=1, step=0.5, value=4),        
                LabeledSlider(app, 'Discount Rate:', 'discount-rate',
                            3, 10, '%',
                            'Enter the Economic Discount Rate, i.e the threshhold rate-of-return for this type of investment.  This rate is a nominal rate *not* adjusted for inflation.',
                            mark_gap=1, step=0.5, value=5),
                LabeledSlider(app, 'Sales Tax:', 'sales-tax',
                            0, 10, '%',
                            'Enter your city/state sales tax.',
                            mark_gap=1, step=0.5, value=0),                            
                LabeledSlider(app, 'Life of Heat Pump:', 'hp-life',
                            5, 30, 'years',
                            'This should be set to 14 years unless there is evidence that a particular model will last shorter or longer than most heat pumps.',
                            mark_gap=2, step=1, value=14),    
                LabeledInput('Annual increase in heating system O&M Cost:', 'annl-om', '$/year', 'Enter a positive value if the cost of maintaining the heating systems with the heat pump is higher than the cost of maintaining the previous system.', inputmode='numeric', value='0'),                            
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
def find_util(city):
    if city_id is None:
        return []
    utils = lib.city_from_id(city_id).ElecUtilities
    return [{'label': util_name, 'value': util_id} for util_name, util_id in utils]
    
@app.callback(Output('div-schedule', 'style'), 
    [Input('elec_input','value')])
def electricalinputs(elec_input, city):
    if elec_input == 'util':
        return {'display': 'block'}
    else:
        return {'display': 'none'}
    
@app.callback(Output('div-man-ez', 'style'), 
    [Input('elec_input','value')])
def electricalinputs_ez(elec_input, city):
    if elec_input == 'ez':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('div-man-adv', 'style'), 
    [Input('elec_input','value')])
def electricalinputs_adv(elec_input, city):
    if elec_input == 'adv':
        return {'display': 'block'}
    else:
        return {'display': 'none'}   
        
@app.callback(Output('blk1_min','children'), [Input('blk0_kwh','value')])
def setblockkwh1(blk0_kwh):
    try:
        return f'{int(blk0_kwh) + 1} -'
    except:
        return None

@app.callback(Output('blk2_min','children'), [Input('blk1_kwh','value')])
def setblockkwh2(blk1_kwh):
    try:
        return f'{int(blk1_kwh) + 1} -'
    except:
        return None

@app.callback(Output('blk3_min','children'), [Input('blk2_kwh','value')])
def setblockkwh3(blk2_kwh):
    try:
        return f'{int(blk2_kwh) + 1} -'
    except:
        return None

@app.callback(Output('fuel_price', 'value'),
    [Input('fuel', 'value'), Input('city','value')])
def find_fuel_price(fuel, city):
    if fuel is None or city is None:
        return None
    the_fuel = lib.fuel_from_id(fuel)
    price_col = the_fuel['price_col']
    
    the_city = lib.city_from_id(city)
    price = np.nan_to_num(the_city[price_col])
    price = np.round(price, 2)
    
    return price 

@app.callback(Output('ht_eff','options'), [Input('fuel', 'value')])
def effic_choices(fuel_id):
    if fuel_id is None:
        return []
    fu = lib.fuel_from_id(fuel_id)
    return [{'label': lbl, 'value': val} for lbl, val in fu.effic_choices]

@app.callback(Output('ht_eff','value'), [Input('ht_eff','options')])
def options(ht_eff):
    if len(ht_eff)>2:
        return ht_eff[1]['value']
    elif len(ht_eff)>0:
        return ht_eff[0]['value']
    else:
        return None

#I've directed this to write into the sp_ht_use box so I can make sure it works, nothing I've tried gets it to update the units label
@app.callback(Output('units-sp_ht_use', 'children'),[Input('fuel','value')])
def updateunits(fuel_id):
    if fuel_id is None:
        return None
    fu2 = lib.fuel_from_id(fuel_id)
    return fu2.unit  
    
@app.callback(Output('jan_elec','value'),[Input('city_id','value')])
def whole_bldg_jan(city_id):
    if city_id is None:
        return None
    jan_elec = lib.city_from_id(city_id).avg_elec_usage[0]
    jan_elec = np.round(jan_elec, 0)
    return jan_elec
    
@app.callback(Output('may_elec','value'),[Input('city_id','value')])
def whole_bldg_may(city_id):
    if city_id is None:
        return None
    may_elec = lib.city_from_id(city_id).avg_elec_usage[4]
    may_elec = np.round(may_elec, 0)
    return may_elec
        
@app.callback(Output('hp-manuf', 'options'), [Input('zones', 'value'), Input('efficient-only', 'values')])
def hp_brands(zones, effic_check_list):
    zone_type = 'Single' if zones==1 else 'Multi'
    manuf_list = lib.heat_pump_manufacturers(zone_type, 'efficient' in effic_check_list)
    return [{'label': brand, 'value': brand} for brand in manuf_list]

@app.callback(Output('hp-model', 'options'), 
              [Input('hp-manuf', 'value'), Input('zones', 'value'), Input('efficient-only', 'values')])
def hp_models(manuf, zones, effic_check_list):
    zone_type = 'Single' if zones==1 else 'Multi'
    model_list = lib.heat_pump_models(manuf, zone_type, 'efficient' in effic_check_list)
    return [{'label': lbl, 'value': id} for lbl, id in model_list]

@app.callback(Output('div1', 'style'), [Input('div-selector', 'value')])
def toggle_container1(selector_value):
    if selector_value == 1:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('div2', 'style'), [Input('div-selector', 'value')])
def toggle_container2(selector_value):
    if selector_value == 2:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('hp-model2', 'options'), 
              [Input('hp-manuf', 'value'), Input('zones', 'value'), Input('efficient-only', 'values')])
def hp_models2(manuf, zones, effic_check_list):
    zone_type = 'Single' if zones==1 else 'Multi'
    model_list = lib.heat_pump_models(manuf, zone_type, 'efficient' in effic_check_list)
    return [{'label': lbl, 'value': id} for lbl, id in model_list]

@app.callback(Output('key-inputs', 'children'), 
    ui_helper.calc_input_objects())
def show_key_inputs(*args):
    vars, extra_vars = ui_helper.inputs_to_vars(args)
    return dedent(f'''
    ```
    Variables:
    {vars}

    Extra Variables:
    {extra_vars}
    ```
    ''')

# -------------------------------------- MAIN ---------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)   # use on Windows computer
