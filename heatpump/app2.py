"""
Heat Pump Calculator Dash Application.
Requires version 0.23 or later of Dash.
"""
import dash
import dash_core_components as dcc
import dash_html_components as html
from .components import LabeledInput, LabeledSlider, LabeledSection, LabeledTextInput, \
    LabeledDropdown, LabeledRadioItems, LabeledChecklist

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

        LabeledRadioItems('Type of Heat Pump: Single- or Multi-zone:',
                          'zones',
                          'Select the number of Indoor Units present on the Heat Pump.',
                          options= [
                              {'label': 'Single Zone', 'value': 1},
                              {'label': 'Multi Zone: 2 zones', 'value': 2},
                              {'label': 'Multi Zone: 3 zones', 'value': 3}],
                          value=1),
        
        LabeledChecklist('Check the Box if Indoor Units are mounted 6 feet or higher on wall:',
                         'indoor-unit-height',
                         options=[{'label': "Indoor Unit mounted 6' or higher", 'value': 'in_ht_6'}],
                         values=[]),

        LabeledInput('Number of Indoor Units:', 
                     'indoor-units',
                     'units',
                     'Enter the number of Heat Pump Indoor Units (heads).'),

        LabeledInput('Floor Area of Building:', 
                     'floor-area',
                     'square feet'),
       
        LabeledSlider('Indoor Temperature:',
                      'indoor-temp',
                      app,
                      '°F',
                      'Enter the Average Indoor Temperature for the Spaces heated by the Heat Pump.',
                      min=60, max=80, step=1, value=71, mark_gap=5),
    ]),

    LabeledSection('Economic Inputs', [

        html.Details(style={'maxWidth': 550}, children=[
            html.Summary('Click Here to see Advanced Economic Inputs'),
            html.Div(style={'marginTop': '3rem'}, children=[
                LabeledSlider('Discount Rate:',
                            'discount-rate',
                            app,
                            '%',
                            'Enter the Economic Discount Rate, i.e the threshhold rate-of-return for this type of investment.  This rate is a nominal rate *not* adjusted for inflation.',
                            min=3, max=10, step=0.5, value=5, mark_gap=1),

                LabeledInput('Floor Area of Building:', 
                            'floor-area',
                            'square feet'),
            ])
        ])

    ]),

    LabeledSection('Results', [
        html.P('Results go Here!')
    ]),

])


if __name__ == '__main__':
    # app.run_server(debug=True)   # use on Windows computer
    app.run_server(debug=True, host='0.0.0.0')   # use on Pixelbook
    