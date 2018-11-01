"""This module is used to create the Dash components that display the
results of the model run.
"""
from textwrap import dedent

import numpy as np
import pandas as pd

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly import tools

from . import ui_helper
from . import hp_model

def generate_table(dataframe, max_rows=50):
    return html.Table(
        # Header
        [html.Tr([html.Th(dataframe.index.name)] + [html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr( [html.Td(dataframe.index[i])] + [
            html.Td('{:,.0f}'.format(dataframe.iloc[i][col])) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


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
    smy['npv_fmt'] = '${:,.0f}'.format(smy['npv']).replace('$-', '-$')   # formatted version of NPV
    smy['irr'] *= 100.   # convert to %
    smy['fuel_savings'] = -smy['fuel_use_chg']
    smy['npv_indicator'] = 'earn' if smy['npv'] >= 0 else 'lose'
    smy['co2_lbs_saved_life'] = smy['co2_lbs_saved'] * inputs['hp_life']
    smy['co2_driving_miles_saved_life'] = smy['co2_driving_miles_saved'] * inputs['hp_life']
    smy['hp_load_frac'] *= 100.   # convert to %

    md_tmpl = dedent('''
    #### Net Present Value:  **{npv_fmt}**

    The Net Present Value of installing an air-source heat pump is estimated to 
    be **{npv_fmt}**. This means that over the course of the life of the equipment you 
    will {npv_indicator} a total of **\${npv_abs:,.0f}** in today's dollars.
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

    # formatted fuel savings
    if smy['fuel_savings'] < 50:
        smy['fuel_savings_fmt'] = '{fuel_savings:.2f}'.format(**smy)
    else:
        smy['fuel_savings_fmt'] = '{fuel_savings:,.0f}'.format(**smy)

    md_tmpl = dedent('''
    #### Annual Heating Fuel Savings: **{fuel_savings_fmt} {fuel_unit}** of {fuel_desc}

    This shows how much heating fuel is saved each year by use of the heat pump. The heat pump
    achieves these savings by **serving {hp_load_frac:.0f}%** of the building's space heating
    load.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    md_tmpl = dedent('''
    #### Annual Increase in Electricity Use: **{elec_use_chg:,.0f} kWh**

    Use of the heat pump adds to the electric use of the building.  Shown here is 
    the annual increase in electricity use.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    md_tmpl = dedent('''
    #### Seasonal Average Heat Pump COP: **{cop:.2f}**

    The Seasonal Average Heat Pump COP indicates the annual average efficiency of the heat pump.
    Conventional Electric Resistance heat (e.g. electric baseboard) would have a COP of 1.0.
    Heat Pumps generally have COPs in excess of 2.0.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    md_tmpl = dedent('''
    #### Electricity and Fuel Prices

    The average cost for the *additional* electricity needed for the heat pump was 
    was **${elec_rate_incremental:.4f}/kWh**.  This accounts for any block rates, and 
    PCE limits that may be present. The fuel price for the fuel saved was 
    **${fuel_price_incremental:.4g}/{fuel_unit}**.  These values include sales taxes.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    md_tmpl = dedent('''
    #### Greenhouse Gas Emissions

    Installing a heat pump is predicted to save **{co2_lbs_saved:,.0f} pounds of CO2** emissions annually, 
    or {co2_lbs_saved_life:,.0f} pounds over the life of the equipment. This is equivalent to a reduction 
    of **{co2_driving_miles_saved:,.0f} miles driven** by an average passenger vehicle annually, 
    or {co2_driving_miles_saved_life:,.0f} miles over the equipment's life.

    ---
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    comps.append(dcc.Markdown(dedent('''
    ### Cash Flow Results

    The graph below shows how the heat pump project impacts cash flow in each of the years
    during the life of the heat pump.  Negative, red, values indicate a net outflow of cash
    due to installing the heat pump, and positive, black, values indicate an net inflow of
    cash due to the heat pump installation.  All values  in this section include sales taxes.
    # ''')))

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
            tickformat='$,.0f',
        ),
        hovermode= 'closest',
    )
    
    gph = dcc.Graph(
        figure=go.Figure(
            data=[negative_flow, positive_flow],
            layout=layout,
        ),
        config=my_config,
        id='gph-1',
    )
    comps.append(gph)

    # Cumulative Cash Flow Graph

    comps.append(dcc.Markdown(dedent('''
    The graph below also shows cash flow but it shows the cumlative impact of the cash
    flow over the life of the heat pump.  A running total of the cash flow impact is
    shown, adjusted for the time-value of money (interest).  When the cumulative cash
    flow exceeds zero (turns black), the heat pump invested has paid itself back 
    with interest.
    ''')))

    df_cash_flow['cum_negative_flow'] = np.where(df_cash_flow.cum_disc_cash_flow < 0, df_cash_flow.cum_disc_cash_flow, 0)
    df_cash_flow['cum_positive_flow'] = np.where(df_cash_flow.cum_disc_cash_flow > 0, df_cash_flow.cum_disc_cash_flow, 0)

    negative_cash_flow = go.Scatter(
        x=df_cash_flow.index,
        y=df_cash_flow.cum_negative_flow,
        name='Cash Flow ($)',
        fill='tozeroy',
        fillcolor='#d7191c',
        line=dict(color='#ffffff'),
        hoverinfo = 'y',
        mode='lines',
    )

    positive_cash_flow = go.Scatter(
        x=df_cash_flow.index,
        y=df_cash_flow.cum_positive_flow,
        name='Cash Flow ($)',
        fill='tozeroy',
        fillcolor='#000000',
        line=dict(color='#ffffff'),
        hoverinfo = 'y',
        mode='lines',
    )

    layout = go.Layout(
        title='Heat Pump Lifetime Cumulative Discounted Cash Flow',
        xaxis=dict(title='Year', fixedrange=True,),
        yaxis=dict(
            title='Annual Discounted Cash Flow ($)', 
            hoverformat='$,.0f',
            fixedrange=True,
            tickformat='$,.0f',
        ),
        hovermode= 'closest',
        showlegend=False,
    )

    gph = dcc.Graph(
        figure=go.Figure(
            data=[negative_cash_flow, positive_cash_flow],
            layout=layout,
        ),
        config=my_config,
        id='gph-2',
    )
    comps.append(gph)

    # Cash Flow Table

    comps.append(dcc.Markdown(dedent('''
    The table below breakdowns the cash flow impacts into components.  All values are dollars.
    Positive numbers indicate a beneficial impact (inflow of cash); negative values indicate
    a detrimental impact (outflow of cash).
    ''')))

    cols = (
        ('initial_cost', 'Initial Cost'),
        ('loan_cost', 'Loan Payments'),
        ('op_cost', 'Operating Cost'),
        ('fuel_cost', 'Heating Fuel Cost'),
        ('elec_cost', 'Electricity Cost'),	
        ('cash_flow', 'Net Cash Flow'),
        ('cum_disc_cash_flow', 'Cumulative Discounted Cash Flow')
    )
    old_cols, new_cols = zip(*cols)
    dfc = df_cash_flow[list(old_cols)].copy()
    dfc.columns = new_cols
    dfc.index.name = 'Year'
    comps.append(generate_table(dfc))

    comps.append(dcc.Markdown('.\n\n### Results by Month'))

    md_tmpl = dedent('''
    ##### Monthly Energy Cost Impacts

    This graph shows how the building's monthly energy costs change due to
    the heat pump.  Both electricity costs and fuel costs are included.
    The dots show the current level of energy cost prior to
    installing the heat pump.  If the heat pump lowers energy cost in the month,
    a green bar drops from the dot down to the new level of energy cost for the
    month.  If the heat pump raises costs in the month (e.g. the added electricity
    cost is more than the fuel cost savings), a red bar extends from the current
    cost dot to the new, higher, energy cost level.  All energy uses are inlcuded
    in the costs, not just space heating.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    # calculate the change in dollars between the base scenario and the heat
    # pump scenario.
    df_mo_dol_chg = df_mo_dol_hp - df_mo_dol_base

    df_mo_dol_chg['cost_savings'] = np.where(
        df_mo_dol_chg.total_dol < 0.0,
        -df_mo_dol_chg.total_dol,
        0.0
    )

    # Note: we make these negative values so bars extend downwards
    df_mo_dol_chg['cost_increases'] = np.where(
        df_mo_dol_chg.total_dol >= 0.0,
        -df_mo_dol_chg.total_dol,
        0.0
    )

    hp_cost = go.Bar(
        x=df_mo_dol_hp.index,
        y=df_mo_dol_hp.total_dol,
        name='', 
        marker=dict(color='#377eb8'),
        hoverinfo = 'y',
    )

    cost_savings = go.Bar(
        x=df_mo_dol_chg.index,
        y=df_mo_dol_chg.cost_savings,
        name='Cost Savings',
        marker=dict(color='#4daf4a'),
        hoverinfo = 'y',
    )

    cost_increases = go.Bar(
        x=df_mo_dol_chg.index,
        y=df_mo_dol_chg.cost_increases,
        name='Cost Increases',
        marker=dict(color='#e41a1c'),
        hoverinfo = 'y',
    )

    no_hp_costs = go.Scatter(
        x=df_mo_dol_base.index,
        y=df_mo_dol_base.total_dol,
        name='Baseline Energy Costs',
        mode='markers',
        marker=dict(color='#000000', size=12),
        hoverinfo = 'y',
    )

    layout = go.Layout(
        title='Energy Costs: Heat Pump vs. Baseline',
        xaxis=dict(title='Month', fixedrange=True,),
        yaxis=dict(
            title='Total Energy Costs', 
            hoverformat='$,.0f',
            fixedrange=True,
            tickformat='$,.0f',
        ),
        barmode='stack',
        hovermode= 'closest',
    )

    gph = dcc.Graph(
        figure=go.Figure(
            data=[hp_cost, cost_savings, cost_increases, no_hp_costs],
            layout=layout,
        ),
        config=my_config,
        id='gph-3',
    )
    comps.append(gph)

    md_tmpl = dedent('''
    ##### Monthly Space Heating Load

    This graph shows how the space heating load of the building varies
    across the months, and it shows what portion of that load is served by
    the heat pump versus the existing heating system.  The units are total 
    MMBtu of heating load placed
    on the building's heating system.  Not all of this load may be served
    by the heat pump, due to heat distribution and capacity limitations of
    the heat pump. This figure does *not* include Domestic Hot Water or any
    other uses of the fuel used for heating.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    hp_load = go.Bar(
        x=df_mo_en_hp.index,
        y=df_mo_en_hp.hp_load_mmbtu, 
        name='Heat Pump Load',
        hoverinfo='y',
    )

    exist_load = go.Bar(
        x=df_mo_en_hp.index,
        y=df_mo_en_hp.secondary_load_mmbtu, 
        name='Load on Existing System',
        hoverinfo='y',
    )

    layout = go.Layout(
        title='Monthly Space Heating Load',
        xaxis=dict(title='Month', fixedrange=True,),
        yaxis=dict(
            title='Estimated Space Heating Load, MMBtu', 
            hoverformat=',.1f',
            fixedrange=True,
        ),
        barmode='stack',
        hovermode= 'closest',
    )

    gph = dcc.Graph(
        figure=go.Figure(
            data=[hp_load, exist_load],
            layout=layout,
        ),
        config=my_config,
        id='gph-4',
    )
    comps.append(gph)

    md_tmpl = dedent('''
    ##### Monthly Electricity and Fuel, Before/After

    This graph shows electricity use and fuel use before and after installation of the heat pump.
    This is total electricity and fuel use, including energy uses beyond just space heating.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    elec_no_hp = go.Scatter(
        x=df_mo_dol_base.index,
        y=df_mo_dol_base.elec_kwh,
        name='Monthly kWh (no Heat Pump)',
        line=dict(
            color='#92c5de',
            width=2,
            dash='dash'
        ),
        hoverinfo='y',
    )

    elec_w_hp = go.Scatter(
        x=df_mo_dol_hp.index,
        y=df_mo_dol_hp.elec_kwh,
        name='Monthly kWh (with Heat Pump)',
        mode='lines+markers',
        marker=dict(color='#0571b0'),
        hoverinfo='y',
    )

    fuel_no_hp = go.Scatter(
        x=df_mo_dol_base.index,
        y=df_mo_dol_base.secondary_fuel_units,
        name='Monthly Fuel Usage (no Heat Pump)',
        line=dict(color='#f4a582',
            width=2,
            dash='dash',
        ),
        hoverinfo='y',
    )

    fuel_w_hp = go.Scatter(
        x=df_mo_dol_hp.index,
        y=df_mo_dol_hp.secondary_fuel_units,
        name='Monthly Fuel Usage (with Heat Pump)',
        mode='lines+markers',
        marker=dict(color='#ca0020'),
        hoverinfo='y',
    )

    fig = tools.make_subplots(rows=2, cols=1)

    fig.append_trace(elec_no_hp, 1, 1)
    fig.append_trace(elec_w_hp, 1, 1)
    fig.append_trace(fuel_no_hp, 2, 1)
    fig.append_trace(fuel_w_hp, 2, 1)

    fig['layout'].update(title='Energy Usage: Heat Pump vs. Baseline')

    fig['layout']['xaxis1'].update(title='Month', fixedrange=True)
    fig['layout']['xaxis2'].update(title='Month', fixedrange=True)
    fig['layout']['yaxis1'].update(
        title='Electricity Use (kWh)', 
        hoverformat=',.0f',
        fixedrange=True,
    )
    yaxis2_title = 'Fuel Use (%s)' % (smy['fuel_unit'])
    fig['layout']['yaxis2'].update(
        title=yaxis2_title, 
        hoverformat='.3g',
        fixedrange=True,
    )
    fig['layout']['hovermode'] = 'closest'

    gph = dcc.Graph(
        figure=fig,
        config=my_config,
        id='gph-5',
    )
    comps.append(gph)

    md_tmpl = dedent('''
    ##### Monthly Heat Pump Efficiency

    This graph shows the efficiency of the heat pump in each month.  Heat Pump
    efficiency is measured as "COP"(Coefficient of Performance).  A COP of 2.5
    means 250% efficient, as compared to electric resistance heat, which is 100%
    efficient.  The heat pump's efficiency improves as the temperature outside
    warms.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    efficiency = [go.Scatter(
        x=df_mo_en_hp.index,
        y=df_mo_en_hp.cop, 
        name='COP',
        mode='lines+markers',
        hoverinfo='y',
    )]

    layout = go.Layout(
        title='Monthly Heat Pump Efficiency, COP',
        xaxis=dict(title='Month', fixedrange=True,),
        yaxis=dict(
            title='COP', 
            hoverformat=',.2f',
            fixedrange=True,
        ),
        hovermode= 'closest',
    )

    gph = dcc.Graph(
        figure=go.Figure(
            data=efficiency,
            layout=layout,
        ),
        config=my_config,
        id='gph-6',
    )
    comps.append(gph)

    md_tmpl = dedent('''
    ##### Monthly Heat Pump Peak Demand

    This graph shows the maximum electrical demand of the heat pump in each
    month of the year.  Units are kilowatts are reflective of the point during
    the month when the heat pumps electrical draw is at its maximum.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    peak_demand = [go.Scatter(
        x=df_mo_en_hp.index,
        y=df_mo_en_hp.hp_kw, 
        name='Peak Demand',
        mode='lines+markers',
        hoverinfo='y',
    )]

    layout = go.Layout(
        title='Monthly Heat Pump Peak Demand, kW',
        xaxis=dict(title='Month', fixedrange=True,),
        yaxis=dict(
            title='Peak Demand, kW', 
            hoverformat=',.2f',
            fixedrange=True,
        ),
        hovermode= 'closest',
    )

    gph = dcc.Graph(
        figure=go.Figure(
            data=peak_demand,
            layout=layout,
        ),
        config=my_config,
        id='gph-7',
    )
    comps.append(gph)

    # Design Heat Load Info

    if smy['max_hp_reached']:
        smy['max_hp_str'] = '*did* deliver its maximum output capacity at some'
    else:
        smy['max_hp_str'] =  '*did not* need to deliver its maximum output capacity at any'

    md_tmpl = dedent('''
    ##### Design Heating Load Information

    An approximate estimate of the design space heating load of this building is
    **{design_heat_load:,.0f} Btu/hour**, not including any domestic hot water load.
    This was based on a Design Outdoor Temperature of **{design_heat_temp:.1f} °F**; 
    approximately 1% of the hours in the year (88 hours) will be colder than this 
    temperature. The design heating load figure does *not* include any safety margin
    and is measured at the output of the heating system.

    The heat pump is estimated to have an output of **{hp_max_capacity_5F:,.0f} Btu/hour at a 5 °F**
    outdoor temperature.  The heat pump will have different maximum output capacities at other
    outdoor temperatures, as the heat pump's efficiency varies with outdoor temperature.
    This energy model shows that the heat pump {max_hp_str} point during the year.
    ''')
    comps.append(dcc.Markdown(md_tmpl.format(**smy)))

    comps.append(html.Hr())

    # Debug information
    debug = html.Details(style={'maxWidth': 550}, children=[
        html.Summary('Click Here for Debug Output'),
        html.Div(style={'marginTop': '3rem'}, children=[
            dcc.Markdown(f"```\n{mod}\n```"),
        ])
    ])

    comps.append(debug)

    return comps
