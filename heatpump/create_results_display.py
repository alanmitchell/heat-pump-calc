"""This module is used to create the Dash components that display the
results of the model run.
"""
from pprint import pformat

import dash_core_components as dcc
import dash_html_components as html

from . import ui_helper
from . import hp_model

def create_results(input_values):
    """Returns a list of Dash components/elements that display
    the restults of the model run.  This list is suitable for
    use as the 'children' of a Div displaying the results.
    'input_values' are a list of the values of all of the Inputs that 
    feed the model calculations.  This comes from a callback. 
    """
    _, vars, _ = ui_helper.inputs_to_vars(input_values)

    # Run the model
    mod = hp_model.HP_model(**vars)
    mod.run()

    # Pull out the results from the model object.
    smy = mod.summary
    df_cash_flow = mod.df_cash_flow
    df_mo_en_base = mod.df_mo_en_base
    df_mo_en_hp = mod.df_mo_en_hp
    df_mo_dol_base = mod.df_mo_dol_base
    df_mo_dol_hp = mod.df_mo_dol_hp

    comps = []
    comps.append(dcc.Markdown(f"#### Results Here!\n\n{pformat(smy)}"))
    comps.append(dcc.Markdown(f"```\n{df_cash_flow}\n```"))
    return comps
