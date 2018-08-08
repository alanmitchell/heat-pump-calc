import dash
import dash_core_components as dcc
import dash_html_components as html
from components import LabeledInput, LabeledSlider, LabeledSection

app = dash.Dash()
app.config.supress_callback_exceptions = True

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Experiments</title>
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
    
    html.H1(children='Heat Pump Calculator'),

    LabeledSection('Location Info', [

        LabeledInput('Number of Indoor Units:', 
                     'indoor-units',
                     'Enter the number of Heat Pump Indoor Units (heads).'),

        LabeledInput('Floor Area of Building, square feet:', 
                     'floor-area'),

        LabeledInput('Number of Building Occupants:', 
                     'occupants',
                     'Enter the number of people living in the building.'),
        
        LabeledSlider('Indoor Temperature, °F:',
                        'indoor-temp',
                        app,
                        'Enter the Average Indoor Temperature for the Spaces heated by the Heat Pump.',
                        min=60, max=80, step=1, value=71, mark_gap=5),


    ])
])


if __name__ == '__main__':
    # app.run_server(debug=True)   # use on Windows computer
    app.run_server(debug=True, host='0.0.0.0')   # use on Pixelbook
    