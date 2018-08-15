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

# -------------------------------------- LAYOUT ---------------------------------------------

app.layout = html.Div(className='container', children=[
    
    html.H1('Alaska Mini-Split Heat Pump Calculator'),

    html.P('Explanation here of what the Calculator does.'),

    LabeledSection('General', [
        LabeledTextInput('Building Name', 'bldg-name', size=50),
        html.P('Enter in any Notes you want to be shown when you print this page.'),
        html.Textarea(style={'width': '100%'}),
    ]),
   
    LabeledSection('Location Info', [

        LabeledDropdown('City where Building is Located:', 'city',
                        options=[{'label': 'Anchorage', 'value': 1}, {'label': 'Fairbanks', 'value': 2}],
                        placeholder='Select City'),

        dcc.Markdown(dedent("""\
            Inputs to Add:

            * All the Electric Utility inputs from before.  Use style={'display': 'none'} to hide a Div,
            and style={'display': 'block'} to show a Div.  This will retain the options present in a
            Dropdown and will preserve the current value of an Inputbox.
            * For the CO2 Slider input, the range should go from 0 pounds/kWh to 4 pounds/kWh, and
            the marks are:  Renewables/Wood = 0, Natural Gas = 1.1, Large Diesel = 1.6, 
            Small Diesel = 1.9, Coal = 3.2
            """)),
    ]),

    LabeledSection('Building Characteristics', [
        dcc.Markdown(dedent("""\
            Inputs to Add:

            * Floor area of Building, excluding Garage, square feet.
            * Year Built Input box.
            * Wall Construction RadioItems: 2x4, 2x6, better than 2x6
            * Fuel Type of Existing Space Heating System (Dropdown).
            * Efficiency of Existing Heating System. RadioItems: call the `fuel_from_id(fuel_id)` function,
            and then create radio items from the list found in the `effic_choices` property of that Series.
            * Type of Heating System for determining Auxiliary Electric use (i.e. fans, pumps, controls).
            RadioItems:  No Fans/Pumps (e.g. wood stove), Hydronic (boiler), Fan-assisted Space Heater (e.g. Toyostove),
            Forced Air Furnace
            * Annual Space Heating Fuel Use in physical units (gallons, CCF, etc.).  But make it clear
            this is an optional input and can be left blank.  If left blank, size, year built, and 
            construction will be used to estimate existing fuel use.
            * Whole Building Electricity Use (without heat pump) in January, kWh.  Default to the value found in the
            `avg_elec_usage` property for this City.  Caution against changing the default if they
            don't have their actual utility bills.
            * Whole Building Electricity Use (without heat pump) in May, kWh.  Default to the value found in the
            `avg_elec_usage` property for this City.
            """)),

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

        dcc.Markdown(dedent("""\
            Inputs to Add:

            * Minimum Operation Temperature of the Heat Pump:  Slider from -20 F to 20 F. Default to 5 F.
            Explain that turn off of the heat pump can either be due to technical limits of the heat pump, 
            or due to the homeowner choosing to not run the heat pump in cold temperatures due to poor efficiency.
            * Let's eliminate the Early Winter shut-off date and Late Winter Turn On date.  I'll just use the
            temperature cutoff to model.
            """)),
    ]),

    LabeledSection('Economic Inputs', [

        html.Details(style={'maxWidth': 550}, children=[
            html.Summary('Click Here to see Advanced Economic Inputs'),
            html.Div(style={'marginTop': '3rem'}, children=[

                dcc.Markdown(dedent("""\
                    Inputs to Add:

                    * The fuel and general inflation rates and discount rate from before.
                    * Sales Tax Rate, default 0.
                    * Heat Pump Life in Years, default 14 years.
                    * Extra O&M cost associated with the Heat Pump, default 0.
                    """)),

                LabeledSlider(app, 'Discount Rate:', 'discount-rate',
                            3, 10, '%',
                            'Enter the Economic Discount Rate, i.e the threshhold rate-of-return for this type of investment.  This rate is a nominal rate *not* adjusted for inflation.',
                            mark_gap=1, step=0.5, value=5),

            ])
        ])

    ]),

    LabeledSection('Test Div Show/Hide', [
        LabeledRadioItems('Select Div to Show:', 'div-selector',
                          options= [
                              {'label': 'Div1', 'value': 1},
                              {'label': 'Div2', 'value': 2}],
                          value=1),
        html.Div(id='div1', children=[
                            'This is Div1',
                            LabeledDropdown('Heat Pump Model:', 'hp-model2',
                                            options=[],
                                            max_width=1000),   # wide as possible
                            LabeledInput('Test Input', 'test-input', 'pounds/kWh')
                            ]),
        html.Div(id='div2', children='This is Div2')
    ]),

    LabeledSection('Results', [
        html.P('Results go Here!')
    ]),

])

# -------------------------------------- CALLBACKS ---------------------------------------------

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
