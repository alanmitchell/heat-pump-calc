import dash
import dash_core_components as dcc
import dash_html_components as html
from os.path import dirname, join, realpath
import logging, logging.handlers
import pandas as pd
from datetime import datetime as dt
import numpy as np

from dash.dependencies import Input, Output, State

from . import library as lib
from . import hp_model

app = dash.Dash(__name__)       # this is the Dash app
server = app.server             # this is the underlying Flask app

# path to this directory
APP_PATH = dirname(realpath(__file__))

# ----- Add a file logger to application

# Log file for the application
LOG_FILE = join(APP_PATH, 'logs', 'hpc.log')

# create a rotating file handler
fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=200000, backupCount=5)
fh.setLevel(logging.INFO)

# create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# add the handler to the logger for the Flask app
server.logger.addHandler(fh)

# -----

app.css.append_css({"external_url": "http://cchrc.org/sites/all/themes/CCHRC/css/heatpumpcalc.css"})

# make the city dropdown, to be inserted into the Layout later.
dd_city = dcc.Dropdown(
            id='city',
            options=[{'label': lbl, 'value': i} for lbl, i in lib.cities()],
            value = '',
            )        


dd_aux_elec = ['No Electricity eg. woodstove', 'Boiler', 'Toyostove/Monitor Heater', 'Furnace, efficient Fan', 'Furnace, older fan']            
            
# electric rate input method selections
elec_inputs = ['Select Utility Rate Schedule','Manual Entry','Manual Entry (Advanced)']

bldg_types = ['Residential', 'Community Building', 'Commercial Building']

comm_pce = ['Yes','No']
          
app.layout = html.Div([
    html.H1('Heat Pump Calculator: Under Construction'),
    html.Label('Please select your city:'),
    html.Div([dd_city], style={'width': '250px', 'display': 'inline-block'}),
    html.Div([
    html.H2('Electric Utility Information'),
    html.Label('Please select your input method:'),
    dcc.RadioItems(id='elec_input',
        options=[
             {'label': i, 'value': i} for i in elec_inputs
        ], value = 'Select Utility Rate Schedule',
    ),
    html.Div([
    html.Div([dcc.Dropdown(id='utility')],id='elec_util'), html.Div([html.Label('PCE:'), dcc.Input(id='pce_val', type='number')],id='costequal'), html.Br(),
    html.Div([dcc.RadioItems(id='bldg_type',
        options=[
             {'label': i, 'value': i} for i in bldg_types
        ], value = 'Select Utility Rate Schedule',
    ),],id='building_type', style={'width': '250px', 'display': 'none'}),
        ]
        ,id='elec-div'),
    html.Div([
    html.Label('Select building type:'),
            dcc.RadioItems(id='bldg_type',
                options=[
             {'label': i, 'value': i} for i in bldg_types
        ]),
        ],id='bld_type'),
    html.Br(),
    html.Div(id='comrescomm'),
    html.Div([html.Label('Pounds of CO2 per kWh of incremental electricity generation'),
    html.Br(),
    dcc.Slider(
        id='co2',
        min=40,
        max=120,
        step=1,
        marks={
        40: 'Large Diesel',
        60: 'Small Diesel',
        80: 'Natural Gas',
        100: 'Hydro/Wind',
        120: 'Coal'}
    ),
    ], id='c02', style={'width': '650px'}),
    ], id='elec-inputs'),
    html.Br(),
    html.Div(id='hidden', style={'display': 'none'}),
    html.Div([
    html.H2('Building Information'),
    html.Label('Heated Floor Area'),
    dcc.Input(id='ht_floor_area', type='number'),
    html.Br(),
    html.Label('Average indoor temperature'),html.Abbr(" &nbsp; ", title="Please choose the average set-point of the thermostat for the home. This should take into account any indoor temperature setbacks that are scheduled."),
    html.Br(),
    dcc.Slider(
        id='ind_temp',
        min=60,
        max=80,
        step=1,
        value=71,
        marks={
        60: '60',
        65: '65',
        70: '70',
        75: '75',
        80: '80'}
    ),
    ],id='bldg_info', style={'width': '650px'}),
    html.Br(),
    html.Div([
    html.H2('Heat Pump Characteristics'),
    html.Label('Select your heat pump manufacturer'),
    dcc.Dropdown(id='manufacturer'),
    html.Label('Select your heat pump model'),
    dcc.Dropdown(id='model'),
    html.Label('How many heads'),
    dcc.Input(id='heads', type='number'), html.Abbr(" &nbsp; ", title="Enter the number of different indoor “heads” or heat distribution units that are installed inside the home."),
    html.Br(),
    html.Label('Indoor units are mounted more than 6\' high on wall'),
    dcc.Checklist(
    id='mount_ht',
    options=[
        {'label': 'Yes', 'value': 'y'},
    ],
    values=['y']
    ), html.Abbr(" &nbsp; ", title="Check this box if the indoor “heads” are mounted higher on the wall; this will affect how well the heat is distributed throughout the home."),
    html.Br(),
    html.Label('Minimum Operation Outdoor Temperature'),
    dcc.Input(id='min_op_temp', type='number'), html.Abbr(" &nbsp; ", title="Please enter the lowest temperature at which the heat pump will continue to operate. This should be available in the unit’s documentation."),
    html.Br(),
    html.Label('Please enter your early winter shut down date and late winter turn on date'),html.Abbr(" &nbsp; ", title="If you turn off your heat pump during the coldest part of winter because it no longer operates efficiently, enter the shut-down and restart dates here. If it operates all year round, leave this section blank."),
    dcc.DatePickerRange(
    id='date-picker-range',
    start_date=dt(2018, 1, 1),
    end_date_placeholder_text='Select a date'
    ),
    html.Br(),
    html.Label('Installed cost of heat pump'),
    dcc.Input(id='inst_cost', type='text'),html.Abbr(" &nbsp; ", title="Please enter the entire cost of the heat pump, including equipment, labor, and incidental costs."),
    html.Br(),
    html.Label('Life of heat pump'),
    dcc.Input(id='hp_life', type='number', value='14'),html.Abbr(" &nbsp; ", title="This should be set to 14 unless there is evidence that a particular model will last shorter or longer than most heat pumps."),
    html.Br(),
    html.Label('Annual increase in heating system O&M Cost ($/year)'),
    dcc.Input(id='annl_om', type='text'), html.Abbr(" &nbsp; ", title="Enter a positive value if the cost of maintaining the heating systems with the heat pump is higher than the cost of maintaining the previous system."),
    ],id='hp_chars', style={'width': '650px'}),
    html.Br(),
    html.Div([
    html.H2('Existing heating system information'),
    html.Label('Select existing heating fuel type'),
        dcc.Dropdown(
                id='fuel',
                options=[{'label': lbl, 'value': i} for lbl, i in lib.fuels()],
                ),
    html.Label('Price per unit'),
    dcc.Input(id='ppu', type='text'),
    html.Br(),
    html.Label('Annual Heating Efficiency'),
    dcc.Input(id='ht_eff', type='text'), html.Abbr(" &nbsp; ", title="Enter the heating system efficiency here. This is often listed as the AFUE on the label."),
    html.Br(),
    html.Label('Auxiliary electricity use from existing heating system:'),html.Abbr(" &nbsp; ", title="Choose the type of heating system you currently have installed. This input will be used to estimate the electricity use by that system."),
    dcc.Dropdown(
        id='aux_elec',
        options=[{'label': i, 'value': i} for i in dd_aux_elec],
        value = 'Toyostove/Monitor Heater'),
    html.Label('Annual space heating fuel cost for building in $'),
    dcc.Input(id='sp_ht_cost', type='text'),
    html.Br(),
    html.Label('Value includes Domestic Hot Water'),
    dcc.Checklist(
    id='incl_dhw',
    options=[
        {'label': 'Yes', 'value': 'y'},
    ],
    values=[]
    ),
    html.Br(),
    html.Label('% heating load accessible or servable to heat pump'),html.Abbr(" &nbsp; ", title="This value describes how much of the house can be heated by the heat pump system. The default value is estimated based on the size of the building and the number of heads."),
    html.Br(),
    dcc.Slider(
        id='pct_load',
        min=0,
        max=100,
        step=10,
        marks={
        0: '0',
        25: '25',
        50: '50',
        75: '75',
        100: '100'}
    ),
    ], id='ht_system', style={'width': '650px'}),
    html.Br(),
    html.Div([
    html.H2('Economic Factors'),
    html.Label('Sales tax:'),
    dcc.Input(id='sales_tx', type='text'),
    html.Br(),
    html.Label('General Inflation Rate %:'),
    dcc.Input(id='inf_rate', type='text', value='2'),html.Abbr(" &nbsp; ", title="The default is the inflation rate used by the U.S. Department of Energy. Change this only in special circumstances."),
    html.Br(),
    html.Label('Heating Fuel Price Inflation Rate %:'),
    dcc.Input(id='fuel_inf_rate', type='text', value='4'),html.Abbr(" &nbsp; ", title="This is the predicted annual increase in the price of the chosen heating fuel, based on U.S. Department of Energy estimates."),
    html.Br(),
    html.Label('Electricity Price Inflation Rate %:'),
    dcc.Input(id='elec_inf_rate', type='text', value='4'),html.Abbr(" &nbsp; ", title="This is the predicted annual increase in the price of electricity in this location, based on U.S. Department of Energy estimates."),
    html.Br(),
    html.Label('Discount Rate %:'),
    dcc.Input(id='disc_rate', type='text', value='5'),html.Abbr(" &nbsp; ", title="This is the rate used to account for the time value of money.  Here are two ways to think of this: 1) the cost of borrowing capital, or 2) the rate of return that you could get if you invested your money in a safe alternative.  The default discount rate of 5% is based on the U.S. Department of Energy’s estimate."),
    ], id='economics', style={'width': '650px'}),
    html.Div(id='display-value'),
    dcc.Markdown(id='results'),

], id='main')

#alan's city series
@app.callback(Output('display-value', 'children'),
    [Input('city', 'value')])
def display_value(value):
    cty = lib.city_from_id(value)
    return html.Pre('Information for selected city:\n\n{}'.format(cty))


# generates the utility selection menu
@app.callback(Output('utility', 'options'),
    [Input('city', 'value')])
def find_util(city):
    series = lib.city_from_id(city)
    menu = series['ElecUtilities']
    util_menu = pd.DataFrame(menu)
    util_menu.columns = ['Utility','ID']
    
    return [{'label' : util_menu.get_value(index, 'Utility'), 'value' : util_menu.get_value(index, 'ID')} for index, row in util_menu.iterrows()]  

#fills pce box
@app.callback(Output('pce_val', 'value'), [Input('utility','value')])
def haspce(utility):
    utl = lib.util_from_id(utility)
    pce_val = np.nan_to_num(utl['PCE'])
    #utl_commercial = utl['IsCommercial']
    return pce_val

#assumes residential
#@app.callback(Output('bldg_type', 'value'), [Input('utility','value')])
#def iscommercial(utility):
#    chk = lib.util_from_id(utility)
#    is_commercial = chk['IsCommercial']
#    return would like to set the value of bldg type to residential....

	
# fuel
@app.callback(Output('ppu', 'value'),
    [Input('fuel', 'value'), Input('city','value')])
def find_util(fuel, city):
    fuels = lib.fuel_from_id(fuel)
    lookup_id = fuels['price_col']
    
    lookup = lib.city_from_id(city)
    price = np.nan_to_num(lookup[lookup_id])
    price = np.round(price,2)
    
    return price  

@app.callback(
    Output('fuel', 'value'),
    [Input('fuel', 'options')])
def set_fuel_value(available_options):
    return available_options[2]['value']
    
#sales tax
@app.callback(Output('sales_tx', 'value'),
    [Input('city','value')])
def find_tax(city):
    city_ent = lib.city_from_id(city)
    muni_tax = city_ent['MunicipalSalesTax']
    muni_tax = np.nan_to_num(city_ent['MunicipalSalesTax'])
    boro_tax = city_ent['BoroughSalesTax']
    boro_tax = np.nan_to_num(city_ent['BoroughSalesTax'])
    sales_tx = muni_tax + boro_tax
    
    return sales_tx
 
@app.callback(Output('ht_eff','value'), [Input('fuel','value')])
def fuel_eff(fuel):
    fuels2 = lib.fuel_from_id(fuel)
    ht_eff = fuels2['effic'] 
    
    return ht_eff
    
#@app.callback(Output('hidden','children'), [Input('utility','value')])
#def haspce(utility):
#    utl = lib.util_from_id(utility)
#    utl_pce = utl['PCE']
#    utl_commercial = utl['IsCommercial']
#    return utl_pce
#
#

@app.callback(Output('comrescomm','children'), [Input('bldg_type','value')])
def pce_use(bldg_type):
    if bldg_type == 'Community Building':
        show = html.Div([        
        html.Label('Has all available Community Building PCE been used in this community?'),
            dcc.RadioItems(id='community_pce',
                options=[{'label': i, 'value': i} for i in comm_pce
                ]),
        html.Br(),]),
    elif bldg_type == 'Residential':
        show = ' '
    elif bldg_type =='Commercial Building':
        show = ' '
    return show
    
@app.callback(
    Output('elec-div', 'children'), [Input('elec_input','value'), Input('city','value')])
def electricalinputs(elec_input, city):
    if elec_input == 'Select Utility Rate Schedule':
        disp = html.Div([dcc.Dropdown(id='utility')],id='elec_util'), html.Div([html.Label('PCE:'), dcc.Input(id='pce_val', type='number')],id='costequal'), html.Br(),
    elif elec_input == 'Manual Entry':
        disp = html.Div([
        html.Table(
                [
                    html.Tr( [html.Label('Enter Electric Rate $/kWh'), html.Td(dcc.Input(id='man_elec_rate',type='text'))] ),
                    html.Tr( [html.Td(html.Label('Enter PCE Rate in $/kWh')), html.Td(dcc.Input(id='man_elec_pce', type='text'))] ),                    
                ]
            ),
    ])
    elif elec_input == 'Manual Entry (Advanced)':
        disp = html.Div([
        html.Label('Enter block rates:'),
        html.Br(),
            html.Table(
                [
                    html.Tr( [html.Th("kWh range"), html.Th("Block kWh"), html.Th("Block rate")] )
                ] +
                [
                    html.Tr( [html.Td("0 -  "), html.Td(dcc.Input(id='block_k', type='text')), html.Td(dcc.Input(id='block_r', type='text'))] ),
                    html.Tr( [html.Td(dcc.Input(id='block_0', type='text')), html.Td(dcc.Input(id='block_k2', type='text')), html.Td(dcc.Input(id='block_r2', type='text'))] ),
                    html.Tr( [html.Td(dcc.Input(id='block_1', type='text')), html.Td(dcc.Input(id='block_k3', type='text')), html.Td(dcc.Input(id='block_r3', type='text'))] ),
                    html.Tr( [html.Td(dcc.Input(id='block_2', type='text')), html.Td(dcc.Input(id='block_k4', type='text')), html.Td(dcc.Input(id='block_r4', type='text'))] ),
                    html.Tr( [html.Td(html.Hr(), colSpan='3')] ),
                    html.Tr( [html.Td('Demand Charge in $/kWh', colSpan='2'), html.Td(dcc.Input(id='demand_charge', type='text'))] ),
                    html.Tr( [html.Td('Customer Charge in $', colSpan='2'), html.Td(dcc.Input(id='customer_charge',type='text'))] ),
                    html.Tr( [html.Td('PCE in $/kWh', colSpan='2'), html.Td(dcc.Input(id='man_elec_pce2',type='text'))] ),
                    
                ]
            ),
        html.Br(),
        ]),
    return disp
  
md_results = '''### Results

#### Key Input Information

Space Heating Fuel Type Info:

```
{}
```

#### Monthly Results

The monthly results are a full Pandas DataFrame, but here are the
results for September:

```
{}
```

#### Annual Results

This is a Pandas Series of Annual Results:

```
{}
```

#### Other Results

More results are forthcoming, including cash flow across the life of the
heat pump and various financial measures.
'''


@app.callback(dash.dependencies.Output('results', 'children'),
              [dash.dependencies.Input('city', 'value')])
def display_results(value):
    calc = hp_model.HP_model()
    fuel = lib.fuel_from_id(calc.fuel_type)
    return md_results.format(
        fuel,
        calc.monthly_results().loc[9],
        calc.annual_results()
    )
  