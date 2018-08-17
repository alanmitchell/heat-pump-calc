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
rd_elec_inputs = ['Select Utility Rate Schedule','Manual Entry','Manual Entry (Advanced)']

rd_bldg_types = ['Residential', 'Community Building', 'Commercial Building']

rd_comm_pce = ['Yes','No']

rd_aux_elec = ['No Fans/Pumps (e.g. wood stove)', 'Hydronic (boiler)', 'Fan-assisted Space Heater (e.g. Toyostove)','Forced Air Furnace']  

rd_units = ['Gal', 'CCF', 'Other']

# -------------------------------------- LAYOUT ---------------------------------------------

app.layout = html.Div(className='container', children=[
    
    html.H1('Alaska Mini-Split Heat Pump Calculator'),

    html.P('Explanation here of what the Calculator does. Credits and logos of sponsoring organizations.'),

    LabeledSection('General', [
        LabeledTextInput('Building Name', 'bldg-name', size=50),
        html.P('Enter in any Notes you want to be shown when you print this page.'),
        html.Textarea(style={'width': '100%'}),
    ]),
   
    LabeledSection('Location Info', [

        LabeledDropdown('City where Building is Located:', 'city',
                        options=[{'label': 'Anchorage', 'value': 1}, {'label': 'Fairbanks', 'value': 293}], #Alan, you originally had 2 for the fbx value which was pulling Adak, I went in and entered the correct id for fbx
                        placeholder='Select City'),
        
        LabeledRadioItems('Input method:', 'elec_input',
                          'Choose Select Utility Rate Schedule if you would like to select a utility based on your location. Select Manual Entry if you would like to manually enter utility and PCE rates. Finally, select Manual Entry (Advanced) if you would like to enter block rates. * A copy of your utility bill will be necessary for both manual entry options.',
                          options=[{'label': i, 'value': i} for i in rd_elec_inputs], 
                          value = [],),
    html.Div([                  
        LabeledDropdown('Select your utility','utility', options=[],placeholder='Select Utility Company'),
        LabeledTextInput('PCE:','pce_val',type='number'),
        ],id='div-schedule',style={'display': 'none'}),

    html.Div([html.Table(
        [
            html.Tr( [html.Label('Enter Electric Rate $/kWh'), html.Td(dcc.Input(id='man_elec_rate',type='text'))] ),
            html.Tr( [html.Td(html.Label('Enter PCE Rate in $/kWh')), html.Td(dcc.Input(id='man_elec_pce', type='text'))] ),                    
        ]
    ),],id='div-man-ez', style={'display': 'none'}),
    
    html.Div([html.Label('Enter block rates:'),
        html.Table(
            [
                html.Tr( [html.Th("kWh range"), html.Th("Block kWh"), html.Th("Block rate")] )
            ] +
            [
                html.Tr( [html.Td("0 -  "), html.Td(dcc.Input(id='block_k', type='text')), html.Td(dcc.Input(id='block_r', type='text'))] ),
                html.Tr( [html.Td(dcc.Input(id='block_0', type='text')), html.Td(dcc.Input(id='block_k2', type='text')), html.Td(dcc.Input(id='block_r2', type='text'))] ),
                html.Tr( [html.Td(dcc.Input(id='block_1', type='text')), html.Td(dcc.Input(id='block_k3', type='text')), html.Td(dcc.Input(id='block_r3', type='text'))] ),
                html.Tr( [html.Td(dcc.Input(id='block_2', type='text')), html.Td(dcc.Input(id='block_k4', type='text')), html.Td(dcc.Input(id='block_r4', type='text'))] ),
                html.Tr( [html.Td('Demand Charge in $/kWh', colSpan='2'), html.Td(dcc.Input(id='demand_charge', type='text'))] ),
                html.Tr( [html.Td('Customer Charge in $', colSpan='2'), html.Td(dcc.Input(id='customer_charge',type='text'))] ),
                html.Tr( [html.Td('PCE in $/kWh', colSpan='2'), html.Td(dcc.Input(id='man_elec_pce2',type='text'))] ),
                
            ]
        ),],id='div-man-adv', style={'display': 'none'}),
        
        LabeledSlider(app, 'Pounds of CO2 per kWh of incremental electricity generation:', 'elec-co2', 
            0, 4, 'pounds/kWh',
            max_width = 800,
            marks = {0: 'Renewables/Wood', 1.1: 'Natural Gas', 1.6: 'Lg Diesel', 1.9: 'Sm Diesel', 3.2: 'Coal' },
            step=0.1, value= 1.6,
            ),
    ]),

    LabeledSection('Building Characteristics', [
        LabeledTextInput('Building Floor Area, excluding garage (ft/sq)', 'ht_floor_area', type='number', size=6),
        LabeledTextInput('Year built', 'yr_blt', type='number', size=4),
        LabeledRadioItems('Wall Construction:', 'wall_const', options=[{'label': '2x4', 'value': 1}, {'label': '2x6', 'value': 2},{'label': 'better than 2x6', 'value': 3}],
                       value = [],),
        LabeledDropdown('Select existing heating fuel type', 'fuel',
                options=[{'label': lbl, 'value': i} for lbl, i in lib.fuels()],
                ),
        LabeledTextInput('Price Per Unit:', 'ppu', type='number'),     
        LabeledDropdown('Efficiency of Existing Heating System','ht_eff', options=[],placeholder='NOT WORKING :('),		
        LabeledRadioItems('Auxiliary electricity use from existing heating system:', 'aux_elec', options=[{'label': i, 'value': i} for i in rd_aux_elec],
        value = 'Fan-assisted Space Heater (e.g. Toyostove)',help_text='Choose the type of heating system you currently have installed. This input will be used to estimate the electricity use by that system.'),
        LabeledTextInput('(Optional) Annual space heating fuel cost for building in physical units','sp_ht_cost', help_text='This value is optional and may be left blank. If left blank, size, year built, and construction will be used to estimate existing fuel use. Please use physical units ex: gallons, CCF, etc.', type='number'),
        LabeledRadioItems('Units:', 'sp_ht_unit', options=[{'label': i, 'value': i} for i in rd_units]),
        LabeledTextInput('Whole Building Electricity Use (without heat pump) in January (kWh):', 'jan_elec', help_text='This defaults to the value found for this City, please don\'t adjust unless you have your utility bill with actual numbers.', type='number'),
        LabeledTextInput('Whole Building Electricity Use (without heat pump) in May (kWh):', 'may_elec', help_text='This defaults to the value found for this City, please don\'t adjust unless you have your utility bill with actual numbers.', type='number'),
        html.Br(),
        LabeledSlider(app, 'Indoor Temperature where Heat Pump is Located:', 'indoor-temp',
                      60, 80, '°F',
                      mark_gap=5, step=1, value=71),
    ]),

    LabeledSection('Heat Pump Info', [
        
        LabeledRadioItems('Type of Heat Pump: Single- or Multi-zone:', 'zones',
                          'Select the number of Indoor Units (heads) installed on the Heat Pump.',
                          options= [
                              {'label': 'Single Zone', 'value': 1},
                              {'label': 'Multi Zone: 2 zones installed', 'value': 2},
                              {'label': 'Multi Zone: 3 zones installed', 'value': 3}],
                          value=1),
        
        LabeledChecklist('Show Most Efficient Units Only?', 'efficient-only',
                         options=[{'label': 'Efficient Only', 'value': 'efficient'}],
                         values=['efficient']),

        LabeledDropdown('Heat Pump Manufacturer:', 'hp-manuf',
                        options=[],
                        max_width=300,
                        placeholder='Select Heat Pump Manufacturer'),   

        LabeledDropdown('Heat Pump Model:', 'hp-model',
                        options=[],
                        max_width=1000,   # wide as possible
                        placeholder='Select Heat Pump Model'),

        LabeledInput('Installed Cost of Heat Pump:', 'hp-cost', 'dollars', 
                     'Include all equipment and labor costs.', value=4500),

        LabeledSlider(app, '% of Heat Pump Purchase Financed with a Loan:', 'pct-financed', 
                      0, 100, '%', 
                      'Select 0 if the purchased is not financed.',
                      mark_gap=10, max_width=700,
                      step=5, value=0),
        LabeledInput('Term of Loan', 'loan-term', 'years',
                     'Numbers of Years to pay off Loan.', value=10),

        LabeledChecklist('Check the Box if Indoor Units are mounted 6 feet or higher on wall:',
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
        LabeledSlider(app, 'Minimum Operating Temperature of Heat Pump:', 'min_op_temp', -20, 20, '°F', help_text='Please enter the lowest outdoor temperature at which the heat pump will continue to operate. This should be available in the unit’s documentation. The turn off of the heat pump can either be due to technical limits of the heat pump, or due to the homeowner choosing to not run the heat pump in cold temperatures due to poor efficiency.', mark_gap=5, step=1, value=5),
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
                LabeledInput('Annual increase in heating system O&M Cost:', 'annl-om', '$/year', 'Enter a positive value if the cost of maintaining the heating systems with the heat pump is higher than the cost of maintaining the previous system.', inputmode='numeric', type='number', value='0'),							
            ])
        ])

    ]),

    LabeledSection('Results', [
        html.P('Results go Here!')
    ]),

    html.Hr(),

    html.P('Some sort of Footer goes here.'),

])

# -------------------------------------- CALLBACKS ---------------------------------------------

@app.callback(Output('utility', 'options'),
    [Input('city', 'value')])
def find_util(city):
    utils = lib.city_from_id(city).ElecUtilities
    return [{'label': util_name, 'value': util_id} for util_name, util_id in utils]

@app.callback(Output('pce_val', 'value'), [Input('utility','value')])
def haspce(utility):
    utl = lib.util_from_id(utility)
    pce_val = np.nan_to_num(utl['PCE'])
    #utl_commercial = utl['IsCommercial']
    return pce_val    
    
@app.callback(
    Output('div-schedule', 'style'), [Input('elec_input','value'), Input('city','value')])
def electricalinputs(elec_input, city):
    if elec_input == 'Select Utility Rate Schedule':
        return {'display': 'block'}
    else:
        return {'display': 'none'}
    
@app.callback(
    Output('div-man-ez', 'style'), [Input('elec_input','value'), Input('city','value')])
def electricalinputs(elec_input, city):
    if elec_input == 'Manual Entry':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(
    Output('div-man-adv', 'style'), [Input('elec_input','value'), Input('city','value')])
def electricalinputs(elec_input, city):
    if elec_input == 'Manual Entry (Advanced)':
        return {'display': 'block'}
    else:
        return {'display': 'none'}   

@app.callback(Output('ppu', 'value'),
    [Input('fuel', 'value'), Input('city','value')])
def find_util(fuel, city):
    fuels = lib.fuel_from_id(fuel)
    lookup_id = fuels['price_col']
    
    lookup = lib.city_from_id(city)
    price = np.nan_to_num(lookup[lookup_id])
    price = np.round(price,2)
    
    return price 

#doesn't work
@app.callback(Output('heat_eff', 'options'),[Input('fuel', 'value')])
def find_eff(fuel):
    heat_eff = lib.fuel_from_id(fuel).effic_choices
    return [{'label': option, 'value': val} for option, val in heat_eff]

@app.callback(Output('jan_elec','value'),[Input('city','value')])
def whole_bldg_jan(city):
    jan_elec = lib.city_from_id(city).avg_elec_usage[0]
    jan_elec = np.round(jan_elec,2)
    return jan_elec
    
@app.callback(Output('may_elec','value'),[Input('city','value')])
def whole_bldg_jan(city):
    may_elec = lib.city_from_id(city).avg_elec_usage[4]
    may_elec = np.round(may_elec,2)
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

# -------------------------------------- MAIN ---------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)   # use on Windows computer
