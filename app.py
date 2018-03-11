import dash
import dash_core_components as dcc
import dash_html_components as html
import os

app = dash.Dash(__name__)
server = app.server

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

# make the city dropdown, to be inserted into the Layout later.
dd_city = dcc.Dropdown(
            id='dropdown',
            options=[{'label': i, 'value': i} for i in ['Anchorage', 'Fairbanks', 'Juneau', 'Bethel']],
            value = 'Anchorage'
          )

app.layout = html.Div([
    html.H2('Heat Pump Calculator: Under Construction'),
    html.Div([dd_city], style={'width': '250px', 'display': 'inline-block'}),
    html.Div(id='display-value')
])

@app.callback(dash.dependencies.Output('display-value', 'children'),
              [dash.dependencies.Input('dropdown', 'value')])
def display_value(value):
    return 'You have selected "{}"'.format(value)

if __name__ == '__main__':
    app.run_server(debug=True)
