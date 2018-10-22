"""This module is used to create the Dash components that display the
results of the model run.
"""
from textwrap import dedent

import numpy as np
import pandas as pd

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from . import ui_helper
from . import hp_model

# This is a dictionary of configuration options for the Plotly 
# graphs.  This removes a number of buttons from the mode bar, primarily.
my_config = dict(
    modeBarButtonsToRemove=['select2d', 'lasso2d', 'sendDataToCloud', 
        'toggleSpikelines', 'hoverClosestCartesian', 'hoverCompareCartesian'],
)

def create_results(input_values):
    """Returns a list of Dash components/elements that display
    the restults of the model run.  This list is suitable for
    use as the 'children' of a Div displaying the results.
    'input_values' are a list of the values of all of the Inputs that 
    feed the model calculations.  This comes from a callback. 
    """
    _, inputs, _ = ui_helper.inputs_to_vars(input_values)

    # Run the model
    mod = hp_model.HP_model(**inputs)
    mod.run()

    # Pull out the results from the model object.
    smy = mod.summary
    df_cash_flow = mod.df_cash_flow
    df_mo_en_base = mod.df_mo_en_base
    df_mo_en_hp = mod.df_mo_en_hp
    df_mo_dol_base = mod.df_mo_dol_base
    df_mo_dol_hp = mod.df_mo_dol_hp

    # This will be the list of children that is returned.  For each graph
    # or Markdown block, and item is added to this list.
    comps = []

    # ------- Summary of Economic Return and Greenhouse Gas  ------------
    
    # Add some items and adjust some in the summary dictionary
    smy['npv_abs'] =  abs(smy['npv'])
    smy['irr'] *= 100.   # convert to %
    smy['npv_indicator'] = 'earn' if smy['npv'] >= 0 else 'lose'
    smy['co2_lbs_saved_life'] = smy['co2_lbs_saved'] * inputs['hp_life']
    smy['co2_driving_miles_saved_life'] = smy['co2_driving_miles_saved'] * inputs['hp_life']

    md_tmpl = dedent('''
    ### Heat Pump Cost Effectiveness

    #### Net Present Value:  **\${npv:,.0f}**

    The Net Present Value of installing an air-source heat pump is estimated to 
    be **\${npv:,.0f}**. This means that over the course of the life of the equipment you 
    will {npv_indicator} **\${npv_abs:,.0f}** in today's dollars.
    ''')

    comps.append(dcc.Markdown(md_tmpl.format(**smy)))
    
    if np.isnan(smy['irr']):
        md_tmpl = dedent('''
        #### Internal Rate of Return:  Not Available

        The heat pump does not save enough money to allow for a calculation of the
        internal rate of return.
        ''')
    else:
        md_tmpl = dedent('''
        #### Internal Rate of Return:  **{irr:.1f}%**

        The internal rate of return on the investment is estimated to be **{irr:.1f}%**. 
        Compare this tax-free investment to your other investment options.
        ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    md_tmpl = dedent('''
    ---

    ### Greenhouse Gas Emissions

    Installing a heat pump is predicted to save {co2_lbs_saved:,.0f} pounds of CO2 emissions annually, 
    or {co2_lbs_saved_life:,.0f} pounds over the life of the equipment. This is equivalent to a reduction 
    of {co2_driving_miles_saved:,.0f} miles driven by an average passenger vehicle annually, 
    or {co2_driving_miles_saved_life:,.0f} miles over the equipment's life.

    ---
    ''')

    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    comps.append(dcc.Markdown('### Cash Flow Results'))

    # Cash Flow Graph
    df_cash_flow['negative_flow'] = np.where(df_cash_flow.cash_flow < 0, df_cash_flow.cash_flow, 0)
    df_cash_flow['positive_flow'] = np.where(df_cash_flow.cash_flow > 0, df_cash_flow.cash_flow, 0)
    
    negative_flow = go.Bar(
        x=df_cash_flow.index,
        y=df_cash_flow.negative_flow,
        name='Cash Outflow', 
        marker=dict(color='#d7191c'),
        hoverinfo = 'y',
    )

    positive_flow = go.Bar(
        x=df_cash_flow.index,
        y=df_cash_flow.positive_flow,
        name='Cash Inflow', 
        marker=dict(color='#000000'),
        hoverinfo = 'y',
    )

    layout = go.Layout(
        title='Heat Pump Cash Flow',
        xaxis=dict(title='Year', fixedrange=True),
        yaxis=dict(
            title='Annual Cash Flow ($)', 
            hoverformat='$,.0f', 
            fixedrange=True,
        ),
        hovermode= 'closest',
    )
    
    gph = dcc.Graph(
        figure=go.Figure(
            data=[negative_flow, positive_flow],
            layout=layout,
        ),
        config=my_config,
    )
    comps.append(dcc.Markdown('Explanation of graph below.'))
    comps.append(gph)

    # Cumulative Cash Flow Graph
    comps.append(dcc.Markdown('##### Cumulative Cash Flow Graph Here'))

    # Cash Flow Table
    comps.append(dcc.Markdown('##### Cash Flow Table'))

    comps.append(dcc.Markdown('Temporary Hack.  Will produce a formatted table later.'))
    dfc = df_cash_flow[['initial_cost', 'loan_cost', 'cash_flow', 'cash_flow_no_pce']]
    comps.append(dcc.Markdown(f"```\n{dfc}\n```"))

    # Monthly Energy Cost Impact
    comps.append(dcc.Markdown('##### Monthly Energy Cost Impact Graph Here'))

    # Energy Related Graphs
    comps.append(dcc.Markdown('##### Monthly Load Graph Here'))
    comps.append(dcc.Markdown('##### Monthly Electricity & Fuel, before/after, Graph Here'))
    comps.append(dcc.Markdown('##### Monthly COP Graph Here'))
    comps.append(dcc.Markdown('##### Markdown with Other Energy Impacts (Design Heating, etc)'))

    return comps
