"""This file holds reusable Dash components that combine labels, help text, and
other features with the standard Dash core components.
"""
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np

def make_label(label, help_text, trailing_item=None):
    """This function returns a HTML Paragraph that contains a text
    label ('label'), possibly a help icon with pop-up help ('help_text'), and possibly
    another HTML component ('trailing_item').
    """
    label_items = [label]
    if len(help_text.strip()):
        label_items.append(html.I(className="fas fa-question-circle"))
    if trailing_item:
        label_items.append(trailing_item)
    return html.P(children=label_items, title=help_text)   

def LabeledSection(label, children):
    """Returns a Div row that contains a label title in the left column ('label')
    and other content in the right column.  'children' should be a list of HTML
    elements and Dash Components to render in the right column.
    """
    return html.Div(children=[
        html.Hr(),
        html.Div(className='row', children=[
            html.P(label, className='two columns section-title'),

            html.Div(className='ten columns', children=children)
        ])
    ])

# -------------------------------------------------------------------------------------------
# All of the following are Dash Components wrapped in a Div that contains
# a label for the component and possibly a help text icon and pop-up text.
# The 'id' parameter is the HTML id of the Dash component.  The Div that contains
# the component is also given an id, which is 'div-' plus the id parameter.
# 'help_text' is the pop-up help text that will be displayed when the mouse is
# hovered over the label.  If 'help_text' is present, a question mark icon is 
# also displayed next to the label. Any extra keyword arguments passed to the
# function are passed to the main Dash component wrapped by the function call.

def LabeledInput(label, id, units='', help_text='', inputmode='numeric', type='number', **kwargs):
    """ 'inputmode' and 'type' are arguments to the dcc.Input component but are
    called out explicitly in the argument list in order to change their default values.
    """

    # make the paragraph element holding the label, help icon, and units suffix.
    para = make_label(label, help_text, html.Span(units, className='label-units'))

    # now insert the actual input control into the correct spot in the children list
    para.children.insert(-1, 
        dcc.Input(id=id, inputmode=inputmode, type=type, 
                  style={'maxWidth': 100, 'marginLeft': 10},
                  **kwargs))
            
    return html.Div(className='labeled-comp', id=f'div-{id}', children=para)

def LabeledTextInput(label, id, help_text='', type='text', **kwargs):
    """ 'type' is an argument to the dcc.Input component but is called out 
    explicitly in the argument list in order to change its default values.
    """
    return html.Div(className='labeled-comp', id=f'div-{id}', children=[
                    make_label(label, help_text),
                    dcc.Input(id=id, type=type, **kwargs)
                    ])

def LabeledSlider(app, label, id, min_val, max_val, units='', help_text='', max_width=500, 
                  mark_gap=None, marks={}, **kwargs):
    """As well as wrapping the Slider with a label, this function adds a dynamic label
    that displays the currently selected value, along with its units ('units').  In order
    to implement this functionality, this function needs access to the main Dash 'app'
    object so that an appropriate callback can be established.
    This function also simplifies the creation of evenly-spaced marks on the Slider by allowing
    you to specify a 'mark_gap' which is the spacing between evenly-spaced marks that start
    at the minimum Slider value ('min_val') and progress to the maximum Slider value ('max_val').
    If you do not pass a value for 'mark_gap', you should provide Slider marks in the 'marks'
    dictionary, which is the conventional method of supplying Slider markers.
    'max_width' specifies the maximum width of the Div containing all of these components.
    """

    # Make the Mark dictionary
    if mark_gap:
        mark_vals = np.arange(min_val, max_val + mark_gap, mark_gap)
        final_marks = {}
        for v in mark_vals:
            if v == int(v):
                v = int(v)
            final_marks[v] = str(v)
    else:
        final_marks = marks

    component = html.Div(id=f'div-{id}', 
                         style={'maxWidth': max_width, 'marginBottom': '4rem'},
                         children=[
                             make_label(label, help_text, html.Span('', id=f'cur-val-{id}', style={'marginLeft': 5})),
                             dcc.Slider(id=id,
                                        marks=final_marks,
                                        min=min_val, max=max_val,
                                        **kwargs)
                         ])
    
    @app.callback(Output(f'cur-val-{id}', 'children'), [Input(id, 'value')])
    def set_cur_val(val):
        return f'Value = {val} {units}'
    
    return component

def LabeledDropdown(label, id, help_text='', max_width=400, **kwargs):
    """'max_width' specifies the maximum width of the Div containing all of these components.
    """
        
    return html.Div(className='labeled-comp', id=f'div-{id}', style={'maxWidth': max_width},
                    children=[
                        make_label(label, help_text),
                        dcc.Dropdown(id=id, **kwargs)
                    ])

def LabeledRadioItems(label, id, help_text='', max_width=400, **kwargs):
    """'max_width' specifies the maximum width of the Div containing all of these components.
    """
        
    return html.Div(className='labeled-comp', id=f'div-{id}', style={'maxWidth': max_width},
                    children=[
                        make_label(label, help_text),
                        dcc.RadioItems(id=id, **kwargs)
                    ])

def LabeledChecklist(label, id, help_text='', max_width=400, **kwargs):
    """'max_width' specifies the maximum width of the Div containing all of these components.
    """
        
    return html.Div(className='labeled-comp', id=f'div-{id}', style={'maxWidth': max_width},
                    children=[
                        make_label(label, help_text),
                        dcc.Checklist(id=id, **kwargs)
                    ])
