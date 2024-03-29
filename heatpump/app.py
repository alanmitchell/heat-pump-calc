"""
Heat Pump Calculator Dash Application.
Requires version 0.23 or later of Dash.
"""
from textwrap import dedent
from pprint import pformat
import time

import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import heatpump.constants
from .components import LabeledInput, LabeledSlider, LabeledSection, \
    LabeledDropdown, LabeledRadioItems, LabeledChecklist
import numpy as np	
from . import library as lib
from . import ui_helper
from . import create_results_display
from .utils import chg_nonnum, is_null, to_float

app = dash.Dash(__name__)
server = app.server             # this is the underlying Flask app

# This is needed to assign callbacks prior to layout being loaded, which
# is done in the LabeledSlider() component.
app.config.suppress_callback_exceptions = True

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
            {%renderer%}
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
    ('Range or Oven', 'cooking'),
)

ELEC_USES_INCLUDED = (
    ('Just Space Heating', 'space'),
    ('Space Heating, Lights, and Appliances', 'all')
)

AUX_ELEC_TYPE = (
    ('No Fans/Pumps (e.g. wood stove)', 'no-fan'),
    ('Hydronic (boiler)', 'boiler'),
    ('Fan-assisted Space Heater (e.g. Toyostove)', 'toyo'),
    ('Forced Air Furnace, Efficient Fan', 'furnace-effic'),
    ('Forced Air Furnace, Standard Fan', 'furnace-std')
)

HP_ZONES = (
    ('Single Zone', 1),
    ('Multi Zone: 2 zones installed', 2),
    ('Multi Zone: 3 zones installed', 3),
    ('Multi Zone: 4 zones installed', 4),
)

HP_SELECTION = (
    ('Simple (Heat Pump Model is Automatically Selected)', 'simple'),
    ('Advanced (You select Manufacturer/Model)', 'advanced'),
)

OFF_MONTHS = (
    ('October', 10),
    ('November', 11),
    ('December', 12),
    ('January', 1),
    ('February', 2),
    ('March', 3),
)

OPEN_DOORS = (
    ('Open Doors', True),
    ('Closed Doors', False),
)

TEMPERATURE_TOLERANCE = (
    ('Bedrooms must be kept at nearly the Same Temperature as Main Spaces', 'low'),
    ('Bedrooms can be as much as 5 degrees Cooler than Main Spaces', 'med'),
    ('Bedrooms can be as much as 10 degrees Cooler than Main Spaces', 'high'),
)

# -------------------------------------- LAYOUT ---------------------------------------------

app.layout = html.Div(className='container', children=[
    
    html.H1('Alaska Mini-Split Heat Pump Calculator', style={'text-align': 'center'}),
    html.Img(id='sponsors', 
        alt='sponsors: Northwest Arctic Borough, Homer Electric, Alaska Energy Authority, AHFC, NANA, NAB, Tagiugmiullu Nunamiullu Housing Authority, AVEC, Alaska Power & Telephone',
        src=app.get_asset_url('sponsors.png')
    ),

    dcc.Markdown(dedent('''
    This calculator allows you to evaluate the possible energy and cost savings from use of a
    [mini-split (ductless) heat pump](https://learn.compactappliance.com/mini-split-heat-pumps/) in
    an Alaskan home or small building.  Fill out the inputs listed below and then click the
    "Calculate" button at the bottom of the page to see the results on the analysis.
    ''')),
    html.P([
    'Where you see the question mark symbol ', html.I(className="fas fa-question-circle"), 
    'additional help for the input is available.  Hover your mouse over the symbol to see the pop-up help.'
    ]),
    dcc.Markdown(dedent('''
    If you would like to reset all inputs to their default values and start over, click
    the Refresh button in your web browser.

    The calculator was primarily built to evaluate retrofitting a mini-split heat pump into
    an existing home with an existing heating system.  However, it can be used to compare
    use of a heat pump in a new home to use of a different heating fuel.  To do a fair economic
    comparison in that situation, for the "Installed Cost of the Heat Pump" input, 
    enter in the *extra* cost of the heat pump relative to the
    alternative heating system; this could be a negative number if the heat pump system is
    less expensive.  This same approach should be used if you are in need of *replacing* your
    existing heating system; enter the additional cost of the heat pump install relative to 
    replacing the existing system.

    **March 2022 Updates**: The calculator now uses fuel and electricity prices from the most
    current AkWarm Home Energy Rating Library (updated every 6 months).  Also, the estimated efficiency
    characteristics for heat pumps were adjusted 10% downward to more closely match measured 
    data from heat pump units in Seward, Alaska.

    For more information on development of this calculator, see [this page.](https://analysisnorth.com/pages/projects.html)
    ''')),
   
    LabeledSection('General', [
        LabeledInput('Building Name (optional)', 'bldg_name', size="50"),
        html.P('Enter in any Notes you want shown when you print this page (optional).'),
        dcc.Textarea(id='notes', style={'width': '100%'}),
    ]),

    LabeledSection('Location Info', [

        LabeledDropdown('City where Building is Located:', 'city_id',
		options=[{'label': lbl, 'value': i} for lbl, i in lib.cities()]),
        
        LabeledRadioItems('Input method:', 'elec_input',
                          'Choose "Select Utility Rate Schedule" if you would like to select a utility based on your location. Select "Manual Entry" if you would like to manually enter utility and PCE rates. Finally, select "Manual Entry (Advanced)" if you would like to enter block rates. * A copy of your utility bill will be necessary for both manual entry options.',
                          options=make_options(ELEC_INPUT_METHOD), value='util'),
        html.Div([
            LabeledDropdown('Select your Utility and Rate Schedule','utility_id', options=[], placeholder='Select Utility Company'),
            dcc.Markdown('', id='util-rate-elements'),
        ], id='div-schedule', style={'display': 'none'}),

        html.Div([html.Table(
            [
                html.Tr( [html.Td(html.Label('Electric Rate:')), html.Td(['$ ', dcc.Input(id='elec_rate_ez', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                html.Tr( [html.Td(html.Label('PCE Rate (only if eligible building):')), html.Td(['$ ', dcc.Input(id='pce_ez', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                html.Tr( [html.Td(html.Label('Customer Charge:')), html.Td(['$ ', dcc.Input(id='customer_chg_ez', type='text', style={'maxWidth': 100}), ' /month'])] ),                    
            ]
        )],id='div-man-ez', style={'display': 'none'}),
        
        html.Div([
                html.Label('Enter block rates:'),
                html.Table([
                    html.Tr( [html.Th("Start kWh"), html.Th("End kWh"), html.Th("Rate, $/kWh")] ),
                    html.Tr( [html.Td(html.P("1 -")), html.Td([dcc.Input(id='blk1_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk1_rate', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk2_min')), html.Td([dcc.Input(id='blk2_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk2_rate', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk3_min')), html.Td([dcc.Input(id='blk3_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk3_rate', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td(html.P('',id='blk4_min')), html.Td([dcc.Input(id='blk4_kwh', type='text', style={'maxWidth': 100}), ' kWh']), html.Td(['$ ', dcc.Input(id='blk4_rate', type='text', style={'maxWidth': 100}), ' /kWh'])] ),
                    html.Tr( [html.Td('Demand Charge:', colSpan='2'), html.Td(['$ ', dcc.Input(id='demand_chg_adv', type='text', style={'maxWidth': 100}), ' /kW/mo'])] ),
                    html.Tr( [html.Td('PCE in $/kWh (only if eligible building)', colSpan='2'), html.Td(['$ ', dcc.Input(id='pce_adv', type='text', style={'maxWidth': 100}), ' /kWh'])] ),              
                    html.Tr( [html.Td('Customer Charge in $/month', colSpan='2'), html.Td(['$ ', dcc.Input(id='customer_chg_adv', type='text', style={'maxWidth': 100}), ' /mo'])] ),
                    ])
            ], id='div-man-adv', style={'display': 'none'}),
        html.Details(style={'maxWidth': 550}, children=[
            html.Summary('Click Here to change Advanced Utility Inputs'),
            html.Div(style={'marginTop': '3rem'}, children=[
                html.Div([
                    html.Hr(),
                    dcc.Checklist(
                        options=[{'label': 'Run Analysis ignoring PCE Electric Rate Assistance', 'value': 'no_pce'}],
                        value=[],
                        id='no_pce_chks'),
                ], id='div-ignore-pce', style={'display': 'none'}),
                html.P('.'),
                LabeledSlider(app, 'Pounds of CO2 released per kWh of additional electricity generation:', 'co2_lbs_per_kwh', 
                    0, 3.3, 'pounds/kWh',
                    help_text='This is used to determine how much CO2 is released due to the electricity consumed by the heat pump.  Pick the type of generation that will be used to produce more electricity in your community. A reasonable default value is provided based on your utility; only change if you have better information.',
                    max_width = 800,
                    marks = {0: 'Renewables/Wood', 1.1: 'Natural Gas', 1.7: 'Lg Diesel', 2: 'Sm Diesel', 2.9: 'Coal' },
                    step=0.1, value= 1.7,
                    ),
            ]),
        ]),
    ]),

    LabeledSection('Building Info', [
        LabeledRadioItems('Type of Building:', 'bldg_type',
                options=make_options(BLDG_TYPE), value='res'),
        LabeledRadioItems('Does the Community typically use all of its Community Building PCE allotment?',
                'commun_all_pce', 
                'Select Yes if, in most months, all of the Community Building PCE is used up by the community.  If so, there will be no extra PCE available for the heat pump kilowatt-hours.',
                options=make_options(YES_NO), value=True,
                labelStyle={'display': 'inline-block'}),
        LabeledInput('Building Floor Area, excluding garage (square feet):', 'bldg_floor_area', 
                units='ft2', size="6"),
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
        LabeledChecklist('Besides Space Heating, what other Appliances use this Fuel type?', 'end_uses_chks',
                options=make_options(END_USES), value=[]),
        html.Div([
            LabeledInput('Number of Occupants in Building using the above Appliances:', 'occupant_count',
                    'people', value=3),
        ], id='div-occupants', style={'display': 'none'}),
        LabeledInput('Fuel Price Per Unit:', 'exist_unit_fuel_cost'), 
        LabeledRadioItems('Efficiency of Existing Heating System:','heat_effic', max_width=500),
        LabeledSlider(app, 'Efficiency of Existing Heating System:', 'heat_effic_slider',
                    40, 100, '%',
                    mark_gap=10, step=1, value=80),
        LabeledRadioItems('Auxiliary electricity use (fans/pumps/controls) from existing heating system:', 
                'aux_elec', 
                options=make_options(AUX_ELEC_TYPE), value='boiler',
                help_text='Choose the type of heating system you currently have installed. This input will be used to estimate the electricity use for fans/pumps/controls of that system.',
                ),
		LabeledInput('Annual Fuel Use (see callback for label)', 'exist_fuel_use', 
                help_text='This value is optional and may be left blank, but it is a big help in making an accurate estimate of the savings from the heat pump. If left blank, size and construction will be used to estimate existing fuel use. Please use physical units ex: gallons, CCF, etc.'),
        html.Div([
            LabeledRadioItems("Does this include Lights and Electrical Appliances, or is this just Space Heating use?",
                    'elec_uses',
                    options=make_options(ELEC_USES_INCLUDED), value='all', max_width=700,
                    ),
        ], id='div-elec-uses', style={'display': 'none'}),
        html.Div([
            html.Hr(),
            dcc.Markdown(dedent('''
            The following inputs asking for January and May electricity use are important in two situations:

            * Your home or building is in Rural Alaska and receives Power Cost Equalization (PCE) limited to 750 kilowatt-hours per month.
            * Your utility has a "block" rate structure where the electricity rate varies depending on how much you use.

            If either one of those is true, review the Video Help below and take time to accurately fill out these inputs.
            Otherwise, these inputs have no effect on the financial payback of a heat pump (although they do affect
            some of the total energy cost graphs in the results section).
            ''')),
            html.A('Video Help for Finding Electricity Usage on Your Bill',
                href='https://soapbox.wistia.com/videos/lheK3bAob2',
                target='_blank'),
            LabeledInput('Whole Building Electricity Use (without heat pump) in January:', 'elec_use_jan', 'kWh', 
                    help_text="This defaults to the value found for this City, don't adjust unless you have your utility bill with actual numbers."),
            LabeledInput('Whole Building Electricity Use (without heat pump) in May:', 'elec_use_may', 'kWh', 
                    help_text="This defaults to the value found for this City, don't adjust unless you have your utility bill with actual numbers."),
            html.Hr(),
        ], id='div-jan-may'),
        html.Br(),
        LabeledSlider(app, 'Heating Temperature Setpoint:', 'indoor_heat_setpoint',
                      60, 80, '°F',
                      mark_gap=5, step=1, value=70),
    ]),
    LabeledSection('Heat Pump Info', [
        
        LabeledRadioItems('Type of Heat Pump: Single- or Multi-zone', 'hp_zones',
                'Select the number of Indoor Units (heads) you expect to install with the Heat Pump.  Note that Single Zone systems are more efficient and less expensive than Multi Zone systems, but may not be able to serve all of the heating load of your building.',
                options=make_options(HP_ZONES), value=1),
        LabeledRadioItems('Heat Pump Selection Method', 'hp_selection',
                'With Simple selection, the calculator models an efficient heat pump sized roughly for your application. With Advanced Selection, you pick the Manufacturer and Model of heat pump.',
                options=make_options(HP_SELECTION), value='simple'),
        html.Div([
            dcc.Markdown('Generic Heat Pump Info Here', id='md-hp-simple'),
        ], id='div-hp-simple', style={'marginTop': '2em', 'marginBottom': '2em'}),
        html.Div([
            LabeledChecklist('In the List Below, Show Most Efficient Heat Pump Models Only?', 'efficient_only',
                    options=[{'label': 'Most Efficient Only', 'value': 'efficient'}],
                    value=['efficient']),
            LabeledDropdown('Heat Pump Manufacturer', 'hp_manuf_id',
                    options=[],
                    max_width=300,
                    placeholder='Select Heat Pump Manufacturer'),   
            LabeledDropdown('Heat Pump Model. See Help Question Mark for detail on Info Presented in the List.', 'hp_model_id',
                    "Shown for each model is the model's heat output at 5 °F Outdoor Temperature; the HSPF, which is a measure of the system's heating efficiency; and model numbers for the system's outdoor and indoor units",
                    options=[],
                    max_width=1000,   # wide as possible
                    placeholder='Select Heat Pump Model',
                    style={'fontSize': 14}),
        ], id='div-hp-advanced', style={'display': 'none'}),
        LabeledInput('Installed Cost of Heat Pump (include applicable sales tax), $', 'capital_cost', '$', 
                'Include all equipment, labor, and applicable sales tax costs.  If this is new construction or your existing heating system needs replacement, only enter the extra cost of the heat pump relative to the alternative heating system.',
                value=4500),
        LabeledInput('Rebates Received for Heat Pump, $', 'rebate_dol', '$',
                'Enter the dollar amount of any rebates you will receive for installation of the heat pump.',
                value=0),
        LabeledSlider(app, '% of Heat Pump Purchase Financed with a Loan', 'pct_financed', 
                0, 100, '%', 
                'Select 0 if the purchased is not financed.',
                mark_gap=10, max_width=700,
                step=1, value=0),
        html.Div([
            LabeledSlider(app, 'Length (Term) of Loan', 'loan_term',
                    3, 15, 'years',
                    'Numbers of Years to pay off Loan.',
                    mark_gap=1, max_width=700,
                    step=1, value=10),
            LabeledSlider(app, 'Loan Interest Rate', 'loan_interest',
                    0, 12, '%',
                    mark_gap=1, max_width=700,
                    step=0.1, value=4),
        ], id='div-loan', style={'display': 'none'}),
        LabeledSlider(app, 'Heat Pump is Turned Off below this Outdoor Temperature:', 
                'low_temp_cutoff', 
                -20, 20, '°F', 
                'Please enter the lowest outdoor temperature at which the heat pump will be operated. Turning off the heat pump at low temperatures can either be due to technical limits of the heat pump, or due to you choosing to not run the heat pump in cold temperatures due to poor efficiency or low heat output.', 
                mark_gap=5, step=1, value=5, max_width=600),
        LabeledChecklist('Select Months when Heat Pump is Turned Off for Entire Month:', 'off_months_chks',
            options=make_options(OFF_MONTHS), value=[], max_width=500),
        html.Hr(),
        html.P(dedent('''
            These next questions will help determine how much of the building's 
            heat load can actually be reached by the Heat Pump.  Often the Heat Pump's indoor units do not
            fully serve all of the spaces in the building.
            ''')),
        LabeledRadioItems("Is All of the Building's Heat currently Provided by one Space Heater like a Toyostove or Wood Stove?",
                'point_source',
                options=make_options(YES_NO), value=False,
                help_text="Answer Yes if one point-source heating system such as a Toyostove or Wood Stove provides All of the Building's heat.  This can be true for small, well-insulated buildings with good heat distribution.",
                ),
        html.Div([
            LabeledSlider(app, 'Percentage of the Home that is Openly Exposed to the Heat Pump Indoor Units:', 
                    'pct_exposed_to_hp', 
                    0, 100, '%', 
                    'Include all the rooms that are openly exposed to the Indoor Units, not connected through a door.', 
                    max_width=700, mark_gap=10, step=1, value=46),
            html.Div([
                html.P(dedent('''
                    For those rooms that are not openly exposed to the heat pump indoor units, the following
                    two questions help determine when the heat pump can successfully provide heat to those rooms.
                    ''')),
                LabeledRadioItems('What is your Tolerance for Cooler Bedroom and Back Room Temperatures?',
                        'bedroom_temp_tolerance',
                        options=make_options(TEMPERATURE_TOLERANCE), value='med',
                        max_width=600),
                LabeledRadioItems('Are Doors typically open to the Bedrooms and Back rooms that do not have a Heat Pump Indoor Unit?',
                        'doors_open_to_adjacent', 
                        'For those rooms that are adjacent to the spaces where the Heat Pump Indoor Units are located, are the doors to those spaces generally left open?',
                        options=make_options(OPEN_DOORS), value=True,
                        max_width=600, labelStyle={'display': 'inline-block'})
            ], id='div-bedrooms'),
        ], id='div-heat-dist'),
    ]),

    LabeledSection('Economic Inputs', [

        LabeledSlider(app, 'Sales Tax (applies to heating fuel and electricity costs):', 'sales_tax',
                    0, 10, '%',
                    'Select your city/state sales tax.  This will be applied to the electricity and fuel prices',
                    mark_gap=1, step=0.1, value=0.0),
        html.Details(style={'maxWidth': 550}, children=[
            html.Summary('Click Here to change Advanced Economic Inputs'),
            html.Div(style={'marginTop': '3rem'}, children=[
                LabeledSlider(app, 'General Inflation Rate:', 'inflation_rate',
                            0, 6, '%/year',
                            'Select the overall inflation rate of goods and services in this community.',
                            mark_gap=1, step=0.1, value=2),
                LabeledSlider(app, 'Heating Fuel Price Inflation Rate:', 'fuel_esc_rate',
                            0, 8, '%/year',
                            'Select the predicted annual increase in the price of the chosen heating fuel at this location.  This rate is a nominal rate *not* adjusted for inflation.',
                            mark_gap=1, step=0.1, value=3),    
                LabeledSlider(app, 'Electricity Price Inflation Rate:', 'elec_esc_rate',
                            0, 8, '%/year',
                            'Select the predicted annual increase in the price of electricity at this location.  This rate is a nominal rate *not* adjusted for inflation.',
                            mark_gap=1, step=0.1, value=2),        
                LabeledSlider(app, 'Discount Rate:', 'discount_rate',
                            3, 12, '%/year',
                            'Select the Economic Discount Rate, i.e the threshhold rate-of-return for this type of investment.  This rate is a nominal rate *not* adjusted for inflation.',
                            mark_gap=1, step=0.1, value=5),
                LabeledSlider(app, 'Life of Heat Pump:', 'hp_life',
                            5, 25, 'years',
                            'Select the number of years that the heat pump will last at this location.  14 years is the DOE estimate.',
                            mark_gap=2, step=1, value=14),    
                LabeledInput('Increase in the heating systems Operation/Maintenance Cost due to Heat Pump install:', 'op_cost_chg', 
                            '$/year', 
                            'Enter a positive value if the cost of maintaining the heating systems with the heat pump is higher than the cost of maintaining the previous system.  Enter a negative number if overall O&M costs are expected to decline.'),
            ])
        ])

    ]),

    LabeledSection('Results', [
        dcc.Markdown(id='md-errors'),
        html.Div([
            html.Button('Calculate Results', id='but-calculate'),
            html.P(dedent('''
            Please note that the inputs and results from your Calculator run will be saved to
            be used to improve the Calculator in the future and to provide data for research
            purposes.  No individual runs will be published, only aggregated results.
            '''))],
            id='div-calculate'
        ),
        html.Div(
            dcc.Markdown('#### Calculating...', id='md-calculating'),
            id='div-calculating'
        ),
        html.Div(id='div-results'),
    ]),

    html.Hr(),

    html.Footer(dcc.Markdown(dedent('''
    This calculator was created by [Analysis North](http://www.analysisnorth.com), 
    [The Cold Climate Housing Research Center](http://cchrc.org), and Arctic Energy Systems.
    The underlying code for this calculator is Open Source and available on 
    [Github](https://github.com/alanmitchell/heat-pump-calc). The calculator was built entirely
    in the [Python](https://www.python.org/) programming language through use of the
    [Dash by Plotly](https://plot.ly/products/dash/) framework. Questions and comments may be 
    sent to Alan Mitchell <alan@analysisnorth.com>. 
    '''))),

    # Storage controls needed for control purposes

    # This one stores the time when the Calculation Inputs last changed.
    dcc.Store(id='store-inputs-ts'),

    # This one stores the time when the Calculation button was clicked.
    dcc.Store(id='store-calc-ts'),

    # Stores the time when the Results Div was updated.
    dcc.Store(id='store-results-ts'),

])

# ------------------ CALLBACKS for Input Configuration ---------------------------

@app.callback(Output('utility_id', 'options'),
    [Input('city_id', 'value')])
def find_util(city_id):
    if city_id is None:
        raise PreventUpdate
    utils = lib.city_from_id(city_id).ElecUtilities
    return [{'label': util_name, 'value': util_id} for util_name, util_id in utils]
    
# Found that when options change need to explicitly set a value
@app.callback(Output('utility_id', 'value'),
    [Input('utility_id', 'options')])
def set_util_value(options):
    # If option list changes, unselect the value
    return None

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

@app.callback(Output('co2_lbs_per_kwh', 'value'),
    [Input('utility_id', 'value')])
def set_co2(utility_id):
    if utility_id is None:
        raise PreventUpdate
    else:
        util = lib.util_from_id(utility_id)
        if is_null(util.CO2):
            return 1.6
        else:
            return round(util.CO2, 1)

@app.callback(Output('div-ignore-pce', 'style'),
    [Input('elec_input', 'value'),
     Input('utility_id', 'value'),
     Input('pce_ez', 'value'),
     Input('pce_adv', 'value')])
def set_ignore_pce_vis(elec_input, utility_id, pce_ez, pce_adv):

    if is_null(elec_input):
        raise PreventUpdate

    if elec_input == 'util':
        if is_null(utility_id):
            raise PreventUpdate
        util = lib.util_from_id(utility_id)
        if chg_nonnum(util.PCE, 0.0) == 0.0:
            return {'display': 'none'}
        else:
            return {'display': 'block', 'marginTop': '1rem'}
    elif elec_input == 'ez':
        if to_float(pce_ez, 0.0) == 0.0:
            return {'display': 'none'}
        else:
            return {'display': 'block', 'marginTop': '1rem'}
    elif elec_input == 'adv':
        if to_float(pce_adv, 0.0) == 0.0:
            return {'display': 'none'}
        else:
            return {'display': 'block', 'marginTop': '1rem'}

@app.callback(Output('util-rate-elements', 'children'),
    [Input('utility_id', 'value')])
def show_rate_elements(util_id):

    if util_id is None:
        return ''

    util = lib.util_from_id(util_id)
    
    s = dedent(f'''
    **Electric Rate Elements for this Utility:**

    Monthly Customer Charge: ${chg_nonnum(util.CustomerChg, 0.0):.2f} /month  
    Demand Charge: ${chg_nonnum(util.DemandCharge, 0.0):.2f} /kW/month  
    Power Cost Equalization: ${chg_nonnum(util.PCE, 0.0):.4f} /kWh  

    *kWh Energy Charges:*  
    ''')
    bottom = 1
    for top, rate in util.Blocks:
        if np.isnan(top):
            top_fmt = 'all'
        else:
            top_fmt = '%.0f' % top 
        s += f"{bottom} - {top_fmt} kWh: ${rate:.4f} /kWh  \n"
        if np.isnan(top):
            break
        else:
            bottom = int(top) + 1
    
    return s

@app.callback(Output('div-commun_all_pce', 'style'),
    [Input('bldg_type', 'value')])
def commun_pce_vis(bldg_type):
    # If Community Building, show this input, although it is irrelevant if there is
    # no PCE in this community.
    if bldg_type == 'commun':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('div-occupants', 'style'),
    [Input('end_uses_chks', 'value')])
def set_occupants_vis(end_uses):
    if len(end_uses) > 0:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('exist_unit_fuel_cost', 'value'),
    [Input('exist_heat_fuel_id', 'value'), Input('city_id','value')])
def find_fuel_price(fuel_id, city_id):

    # Situations where there is no price to fill in
    if fuel_id is None or fuel_id == heatpump.constants.ELECTRIC_ID or city_id is None:
        return ''

    the_fuel = lib.fuel_from_id(fuel_id)
    price_col = the_fuel['price_col']
    the_city = lib.city_from_id(city_id)
    price = np.nan_to_num(the_city[price_col])
    price = np.round(price, 2)
    
    return price 

@app.callback(Output('div-exist_unit_fuel_cost', 'style'),
    [Input('exist_heat_fuel_id', 'value')])
def hide_fuel_cost(fuel_id):
    if fuel_id == heatpump.constants.ELECTRIC_ID:
        return {'display': 'none'}
    else:
        return {'display': 'block'}

@app.callback(Output('heat_effic','options'), 
    [Input('exist_heat_fuel_id', 'value')])
def effic_choices(fuel_id):
    if fuel_id is None:
        return []
    fu = lib.fuel_from_id(fuel_id)
    choices = [{'label': lbl, 'value': val} for lbl, val in fu.effic_choices]
    choices += [{'label': 'Manual Entry', 'value': 'manual'}]
    return choices

@app.callback(Output('div-elec-uses', 'style'),
    [Input('exist_heat_fuel_id', 'value'), Input('exist_fuel_use', 'value')])
def hide_elec_uses_included(fuel_id, exist_use):
    if fuel_id == heatpump.constants.ELECTRIC_ID and exist_use != '' and exist_use != None:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('heat_effic','value'), [Input('heat_effic','options')])
def options(ht_eff):
    if len(ht_eff)>2:
        return ht_eff[1]['value']
    elif len(ht_eff)>0:
        return ht_eff[0]['value']
    else:
        return None

@app.callback(Output('div-heat_effic_slider', 'style'),
    [Input('heat_effic', 'value')])
def heat_effic_vis(val):
    if val == 'manual':
        return {'display': 'block', 'marginBottom': '4rem'}
    else:
        return {'display': 'none'}

@app.callback(Output('units-exist_fuel_use', 'children'),[Input('exist_heat_fuel_id','value')])
def update_use_units(fuel_id):
    if fuel_id is None:
        raise PreventUpdate
    fuel = lib.fuel_from_id(fuel_id)
    return fuel.unit + ' per year' 

@app.callback(Output('units-exist_unit_fuel_cost', 'children'),[Input('exist_heat_fuel_id','value')])
def update_price_units(fuel_id):
    if fuel_id is None:
        raise PreventUpdate
    fuel = lib.fuel_from_id(fuel_id)
    return f'$ / {fuel.unit}'

@app.callback(Output('aux_elec', 'value'),
    [Input('exist_heat_fuel_id', 'value')])
def set_aux_elec(fuel_id):
    # Force No Aux use with Electric Heat, otherwise don't 
    # change setting.
    if fuel_id == heatpump.constants.ELECTRIC_ID:
        return 'no-fan'
    else:
        raise PreventUpdate

@app.callback(Output('div-aux_elec', 'style'),
    [Input('exist_heat_fuel_id', 'value')])
def hide_aux_elec(fuel_id):
    if fuel_id == heatpump.constants.ELECTRIC_ID:
        return {'display': 'none'}
    else:
        return {'display': 'block'}

@app.callback(Output('div-heat-dist', 'style'),
    [Input('point_source', 'value')])
def hide_heat_dist(point_source):
    if point_source:
        return {'display': 'none'}
    else:
        return {'display': 'block'}

@app.callback(Output('label-exist_fuel_use', 'children'),
    [Input('exist_heat_fuel_id', 'value')])
def label_fuel_use(fuel_id):
    if fuel_id == heatpump.constants.ELECTRIC_ID:
        return 'Total Annual Electricity Use of the building.  (Optional, but very helpful!):'
    else:
        return 'Annual Fuel Use for the building including space heating and any other appliances that use that same fuel. (Optional, but very helpful for an accurate estimate of heat pump savings, particularly if your building is super-efficient or very inefficient.):'

@app.callback(Output('elec_use_jan','value'),
    [Input('city_id','value'), Input('exist_heat_fuel_id', 'value')])
def whole_bldg_jan(city_id, fuel_id):
    if city_id is None:
        raise PreventUpdate
    if fuel_id == heatpump.constants.ELECTRIC_ID:
        return ''   # Blank it out so no errors can occur once it is hidden
    jan_elec = lib.city_from_id(city_id).avg_elec_usage[0]
    jan_elec = np.round(jan_elec, 0)
    return jan_elec
    
@app.callback(Output('elec_use_may','value'),
    [Input('city_id','value'), Input('exist_heat_fuel_id', 'value')])
def whole_bldg_may(city_id, fuel_id):
    if city_id is None:
        raise PreventUpdate
    if fuel_id == heatpump.constants.ELECTRIC_ID:
        return ''   # Blank it out so no errors can occur once it is hidden
    may_elec = lib.city_from_id(city_id).avg_elec_usage[4]
    may_elec = np.round(may_elec, 0)
    return may_elec

@app.callback(Output('div-jan-may', 'style'),
    [Input('exist_heat_fuel_id', 'value')])
def hide_jan_use(fuel_id):
    if fuel_id == heatpump.constants.ELECTRIC_ID:
        return {'display': 'none'}
    else:
        return {'display': 'block'}

@app.callback(Output('div-garage_heated_by_hp', 'style'), 
    [Input('garage_stall_count','value')])
def garage_heated(stalls):
    if stalls > 0:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('div-hp-simple', 'style'),
    [Input('hp_selection', 'value')])
def show_simple_hp(hp_selection):
    if hp_selection=='simple':
        return {'display': 'block', 'marginTop': '2em', 'marginBottom': '3em'}
    else:
        return {'display': 'none'}

@app.callback(Output('md-hp-simple', 'children'),
    [Input('hp_zones', 'value')])
def show_simple_model(hp_zones):
    if is_null(hp_zones):
        return ''
    else:
        # The library knows how to return generic models for 1 through 4
        # zones by passing the negative zone count.
        hpmod = lib.heat_pump_from_id(-hp_zones)
        return dedent(f'''
        **Heat Pump Characteristics Used in Calculator:**

        *HSPF (a Rating of Heating Efficiency):* **{hpmod.hspf:.1f}**  
        *Maximum Heat Output at 5 °F:* **{hpmod.capacity_5F_max:,.0f} BTUs per hour**
        ''')

@app.callback(Output('div-hp-advanced', 'style'),
    [Input('hp_selection', 'value')])
def show_advanced_hp(hp_selection):
    return {'display': 'block'} if hp_selection=='advanced' else {'display': 'none'}

@app.callback(Output('hp_manuf_id', 'options'), 
    [Input('hp_zones', 'value'), Input('efficient_only', 'value')])
def hp_brands(zones, effic_check_list):
    zone_type = 'Single' if zones==1 else 'Multi'
    manuf_list = lib.heat_pump_manufacturers(zone_type, 'efficient' in effic_check_list)
    return [{'label': brand, 'value': brand} for brand in manuf_list]

# Found that when options change need to explicitly set a value
@app.callback(Output('hp_manuf_id', 'value'),
    [Input('hp_manuf_id', 'options')])
def set_manuf_value(options):
    # If option list changes, unselect the value
    return None

@app.callback(Output('hp_model_id', 'options'), 
              [Input('hp_manuf_id', 'value'), Input('hp_zones', 'value'), Input('efficient_only', 'value')])
def hp_models(manuf, zones, effic_check_list):
    zone_type = 'Single' if zones==1 else 'Multi'
    model_list = lib.heat_pump_models(manuf, zone_type, 'efficient' in effic_check_list)
    return [{'label': lbl, 'value': id} for lbl, id in model_list]

# Found that when options change need to explicitly set a value
@app.callback(Output('hp_model_id', 'value'),
    [Input('hp_model_id', 'options')])
def set_model_value(options):
    # If option list changes, unselect the value
    return None

@app.callback(Output('div-loan', 'style'), 
    [Input('pct_financed','value')])
def loan_inputs(pct_financed):
    if pct_financed > 0:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(Output('pct_exposed_to_hp', 'value'),
    [Input('hp_zones', 'value'), Input('point_source', 'value')])
def set_pct_exposed(zones, point_source):
    if point_source:
        return 100
    else:
        return (46, 66, 86, 100)[zones - 1]  # corresponding to 1 - 4 zones

@app.callback(Output('capital_cost', 'value'),
    [Input('hp_zones', 'value'), Input('city_id', 'value')])
def set_capital_cost(zones, city_id):
    cost = (4000, 6200, 8200, 10200)[zones - 1]
    if city_id is None:
        return cost
    else:
        # Factor in Improvement Cost Level for the City
        cost_level = lib.city_from_id(city_id).ImprovementCostLevel
        # Each cost level is the same percentage above the one prior.
        # Assume highest level (level 5) is 1.6 x lowest level.
        cost_mult = 1.6 ** 0.25
        return round(cost * cost_mult ** (cost_level - 1), 0)

@app.callback(Output('div-bedrooms', 'style'),
    [Input('pct_exposed_to_hp', 'value')])
def set_bedroom_vis(pct_exposed):
    if pct_exposed == 100:
        return {'display': 'none'}
    else:
        return {'display': 'block'}

@app.callback(Output('sales_tax', 'value'),
    [Input('city_id', 'value')])
def set_sales_tax(city_id):
    if city_id is None:
        return 0.0
    city = lib.city_from_id(city_id)
    sales_tax = chg_nonnum(city.MunicipalSalesTax, 0.0) + chg_nonnum(city.BoroughSalesTax, 0.0)
    sales_tax = round(sales_tax * 100.0, 1)  # express in % and round to nearest 0.1%
    return sales_tax

# -------------- Callbacks Related to Calculation Mechanics --------------

def invalid_ts(ts):
    return (ts is None or ts<=0)

@app.callback(Output('store-inputs-ts', 'data'),
    ui_helper.calc_input_objects())
def inputs_ts(*args):
    # Store time inputs changed
    return {'ts': time.time()}

@app.callback(Output('store-calc-ts', 'data'),
    [Input('but-calculate', 'n_clicks')])
def calc_ts(clicks):
    # Store time that Calculate was clicked.
    if clicks is None:
        raise PreventUpdate
    return {'ts': time.time()}

@app.callback(Output('store-results-ts', 'data'),
    [Input('div-results', 'children')],)
def results_ts(children):
    # Store time results changed.
    return {'ts': time.time()}

@app.callback(Output('md-errors', 'children'),
    ui_helper.calc_input_objects())
def list_errors(*args):
    # Returns a Markdown string containing the input error list.
    errors, _, _ = ui_helper.inputs_to_vars(args)
    if len(errors)==0:
        return ''
    error_md = '#### Please Correct the following Input Problems:\n\n'
    for e in errors:
        error_md += f'* {e}\n'
    return error_md

@app.callback(Output('div-calculate', 'style'),
    [Input('store-calc-ts', 'modified_timestamp'),
     Input('store-inputs-ts', 'modified_timestamp'),
     Input('md-errors', 'children')])
def set_calc_visibility(ts_calc, ts_inputs, md_error_children):
    # Sets visibility of Calculate Button
    # print('here', md_error_children, ts_calc, ts_inputs)
    if md_error_children is None or len(md_error_children)>0:
        return {'display': 'none'}
    else:
        if invalid_ts(ts_calc) or ts_calc < ts_inputs:
            return {'display': 'block'}
        else:
            return {'display': 'none'}

@app.callback(Output('div-calculating', 'style'),
    [Input('store-calc-ts', 'modified_timestamp'),
     Input('store-results-ts', 'modified_timestamp')
    ])
def set_calc_indicator_vis(ts_calc, ts_results):
    # Set visibility of the "Calculating..." indicator.
    if invalid_ts(ts_calc):
        return {'display': 'none'}
    elif invalid_ts(ts_results):
        return {'display': 'block'}
    else:
        if ts_calc >= ts_results:
            return {'display': 'block'}
        else:
            return {'display': 'none'}

@app.callback(Output('div-results', 'style'),
    [Input('store-inputs-ts', 'modified_timestamp'),
     Input('store-results-ts', 'modified_timestamp')
    ])
def results_vis(ts_inputs, ts_results):
    # Sets visibility of Results
    if invalid_ts(ts_results) or invalid_ts(ts_inputs):
        return {'display': 'none'}
    else:
        if ts_results >= ts_inputs:
            return {'display': 'block'}  
        else:
            return {'display': 'none'}

@app.callback(Output('div-results', 'children'),
    [Input('but-calculate', 'n_clicks')], ui_helper.calc_state_objects())
def update_results(clicks, *args):
    # Updates the Results Display
    if clicks is None:
        raise PreventUpdate
    return create_results_display.create_results(args)

# -------------------------------------- MAIN ---------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)   # use on Windows computer
