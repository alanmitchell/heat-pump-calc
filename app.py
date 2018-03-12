import dash
import dash_core_components as dcc
import dash_html_components as html
import os

import library

app = dash.Dash(__name__)
server = app.server
server.debug = True

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

# make the city dropdown, to be inserted into the Layout later.
dd_city = dcc.Dropdown(
            id='dropdown',
            options=[{'label': lbl, 'value': i} for lbl, i in library.cities()],
            value = 51,
          )

app.layout = html.Div([
    html.H2('Heat Pump Calculator: Under Construction'), 
    html.Div([dd_city], style={'width': '250px', 'display': 'inline-block'}),
    html.Div(id='display-value')
])

@app.callback(dash.dependencies.Output('display-value', 'children'),
              [dash.dependencies.Input('dropdown', 'value')])
def display_value(value):
    cty = library.city_from_id(value)
    return html.Pre(str(cty))

if __name__ == '__main__':
    app.run_server(debug=True)
