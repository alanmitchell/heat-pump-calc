import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash()

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

def labeled_input(label, id, help_text='', input_type='number'):
    
    label_items = [label + ' ']
    if len(help_text.strip()):
        label_items.append(html.I(className="fas fa-question-circle", title=help_text))
        
    return html.Div(className='labeled-comp', children=[
                html.P(children=label_items),
                dcc.Input(id=id, type=input_type),
            ])

def input_section(label, children):
    return [
        html.Hr(),
        html.Div(className='row', children=[
            html.P(label, className='three columns section-title'),

            html.Div(className='nine columns', children=children)
        ])
    ]

app.layout = html.Div(className='container', children=[
    
    html.H1(children='Heat Pump Calculator'),

    *input_section('Location Info', [

        labeled_input('Number of Indoor Units:', 
                      'indoor-units',
                      'Enter the number of Heat Pump Indoor Units (heads).'),

        labeled_input('Floor Area of Building:', 
                      'floor-area'),

        labeled_input('Number of Building Occupants:', 
                      'occupants',
                      'Enter the number of people living in the building.'),            
    ])
])

if __name__ == '__main__':
    # app.run_server(debug=True)   # use on Windows computer
    app.run_server(debug=True, host='0.0.0.0')   # use on Pixelbook
    