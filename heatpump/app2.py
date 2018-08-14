"""
Heat Pump Calculator Dash Application.
Requires version 0.23 or later of Dash.
"""
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from .components import LabeledInput, LabeledSlider, LabeledSection, LabeledTextInput, \
    LabeledDropdown, LabeledRadioItems, LabeledChecklist
from . import library as lib

app = dash.Dash()
app.config.supress_callback_exceptions = True

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

app.layout = html.Div(className='container', children=[
    
    html.H1('Mini-Split Heat Pump Calculator'),

    LabeledSection('General', [
        LabeledTextInput('Building Name', 'bldg-name', size=50),
        html.P('Enter in any Notes you want to be shown when you print this page.'),
        html.Textarea(style={'width': '100%'}),
    ]),
    
    LabeledSection('Location Info', [

        LabeledDropdown('City where Building is Located:', 'city',
                        options=[{'label': 'Anchorage', 'value': 1}, {'label': 'Fairbanks', 'value': 2}],
                        placeholder='Select City'),
        
        LabeledInput('Floor Area of Building:', 'floor-area',
                     'square feet'),
       
        LabeledSlider(app, 'Indoor Temperature:', 'indoor-temp',
                      60, 80, '°F',
                      'Enter the Average Indoor Temperature for the Spaces heated by the Heat Pump.',
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

        LabeledChecklist('Check the Box if Indoor Units are mounted 6 feet or higher on wall:',
                         'indoor-unit-height',
                         'If most or all of the heat-delivering Indoor Units are mounted high on the wall, check this box.  High mounting of Indoor Units slightly decreases the efficiency of the heat pump.',
                         max_width=500,
                         options=[{'label': "Indoor Unit mounted 6' or higher", 'value': 'in_ht_6'}],
                         values=['in_ht_6']),
        
    ]),

    LabeledSection('Economic Inputs', [

        html.Details(style={'maxWidth': 550}, children=[
            html.Summary('Click Here to see Advanced Economic Inputs'),
            html.Div(style={'marginTop': '3rem'}, children=[
                LabeledSlider(app, 'Discount Rate:', 'discount-rate',
                            3, 10, '%',
                            'Enter the Economic Discount Rate, i.e the threshhold rate-of-return for this type of investment.  This rate is a nominal rate *not* adjusted for inflation.',
                            mark_gap=1, step=0.5, value=5),

                LabeledInput('Floor Area of Building:', 
                            'floor-area',
                            'square feet'),
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
                                            max_width=1000)   # wide as possible
                            ]),
        html.Div(id='div2', children='This is Div2')
    ]),

    LabeledSection('Results', [
        html.P('Results go Here!')
    ]),

])

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

if __name__ == '__main__':
    app.run_server(debug=True)   # use on Windows computer
    