import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np

# Display utility functions
def _merge(a, b):
    return dict(a, **b)


def _omit(omitted_keys, d):
    return {k: v for k, v in d.items() if k not in omitted_keys}


# Custom Display Components
def Card(children, **kwargs):
    return html.Section(
        children,
        style=_merge({
            'padding': 20,
            'margin': 5,
            'borderRadius': 5,
            'border': 'thin lightgrey solid',

            # Remove possibility to select the text for better UX
            'user-select': 'none',
            '-moz-user-select': 'none',
            '-webkit-user-select': 'none',
            '-ms-user-select': 'none'
        }, kwargs.get('style', {})),
        **_omit(['style'], kwargs)
    )


def FormattedSlider(**kwargs):
    return html.Div(
        style=kwargs.get('style', {}),
        children=dcc.Slider(**_omit(['style'], kwargs))
    )


def NamedSlider(name, **kwargs):
    return html.Div(
        style={'padding': '20px 10px 25px 4px'},
        children=[
            html.P(f'{name}:'),
            html.Div(
                style={'margin-left': '6px'},
                children=dcc.Slider(**kwargs)
            )
        ]
    )


def NamedDropdown(name, **kwargs):
    return html.Div(
        style={'margin': '10px 0px'},
        children=[
            html.P(
                children=f'{name}:',
                style={'margin-left': '3px'}
            ),

            dcc.Dropdown(**kwargs)
        ]
    )


def NamedRadioItems(name, **kwargs):
    return html.Div(
        style={'padding': '20px 10px 25px 4px'},
        children=[
            html.P(children=f'{name}:'),
            dcc.RadioItems(**kwargs)
        ]
    )

def LabeledInput(label, id, help_text='', inputmode='numeric', type='number', **kwargs):
    
    label_items = [label + ' ']
    if len(help_text.strip()):
        label_items.append(html.I(className="fas fa-question-circle"))
        
    return html.Div(className='labeled-comp', id=f'div-{id}',children=[
                html.P(children=label_items, title=help_text),
                dcc.Input(id=id, inputmode=inputmode, type=type, 
                    **_omit(['help_text', 'inputmode', 'type'], kwargs)),
            ])

def LabeledSlider(
    label, id, app, units, help_text='', max_width=500, mark_gap=None, marks={},
    **kwargs):

    # Make the Mark dictionary
    if mark_gap:
        mark_vals = np.arange(kwargs['min'], kwargs['max'] + mark_gap, mark_gap)
        final_marks = {}
        for v in mark_vals:
            if v == int(v):
                v = int(v)
            final_marks[v] = str(v)
    else:
        final_marks = marks

    label_items = [label + ' ']
    if len(help_text.strip()):
        label_items.append(html.I(className="fas fa-question-circle"))
    label_items.append(html.Span('', id=f'cur-val-{id}'))

    component = html.Div(id=f'div-{id}', 
                         style={'maxWidth': max_width, 'marginBottom': '4rem'},
                         children=[
                             html.P(children=label_items, title=help_text),
                             dcc.Slider(id=id,
                                        marks=final_marks,
                                        **_omit(['help_text', 'max_width', 'mark_gap', 'marks'], kwargs)),
                         ])
    
    @app.callback(Output(f'cur-val-{id}', 'children'), [Input(id, 'value')])
    def set_cur_val(val):
        return f'Value = {val} {units}'
    
    return component


def LabeledSection(label, children):
    return html.Div(children=[
        html.Hr(),
        html.Div(className='row', children=[
            html.P(label, className='three columns section-title'),

            html.Div(className='nine columns', children=children)
        ])
    ])
