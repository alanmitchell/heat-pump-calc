import dash
import dash_core_components as dcc
import dash_html_components as html
from os.path import dirname, join, realpath
import logging, logging.handlers

from . import library as lib

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

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

# make the city dropdown, to be inserted into the Layout later.
dd_city = dcc.Dropdown(
            id='dropdown',
            options=[{'label': lbl, 'value': i} for lbl, i in lib.cities()],
            value = 1,
          )

app.layout = html.Div([
    html.H2('Heat Pump Calculator: Under Construction'), 
    html.Div([dd_city], style={'width': '250px', 'display': 'inline-block'}),
    html.Div(id='display-value')
])

@app.callback(dash.dependencies.Output('display-value', 'children'),
              [dash.dependencies.Input('dropdown', 'value')])
def display_value(value):
    cty = lib.city_from_id(value)
    return html.Pre('Information for selected city:\n\n{}'.format(cty))
