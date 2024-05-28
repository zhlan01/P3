import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import pandas as pd
from app import *

about_markdown = """
This module is a python-based implementation of the functionality of the Joachim Goedhart team’s literature. You can get more information about the setup, use, instructions and details of each function in the literature, a R language version, which is a free open-source web-based app named VolcaNoseR.

VolcaNoseRis available online at: [https://huygens.science.uva.nl/VolcaNoseR](https://huygens.science.uva.nl/VolcaNoseR) or at: [https://goedhart.shinyapps.io/VolcaNoseR/](https://goedhart.shinyapps.io/VolcaNoseR/). The source code of the current version (v1.0.3) is archived at Zenodo.org: [https://doi.org/10.5281/zenodo.4002791](https://doi.org/10.5281/zenodo.4002791). An up-to-date version is available at Github together with information on how to install and run the app locally: [https://github.com/JoachimGoedhart/VolcaNoseR](https://github.com/JoachimGoedhart/VolcaNoseR).

You can read and cite the original paper from: Goedhart J, Luijsterburg MS. (2020). VolcaNoseR is a web app for creating, exploring, labeling and sharing volcano plots. Scientific reports, 10(1), 20560. [https://doi.org/10.1038/s41598-020-76603-3](https://doi.org/10.1038/s41598-020-76603-3).

We would like to thank Joachim Goedhart and Martijn S. Luijsterburg that contributed the R language version, and everyone that give us advice to improve the platform.

You can contact us by email acm_ict@163.com.
"""

Layout = dbc.Container([
    LayoutHead_VolcaNoseR,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("About"),
                        html.P("PVV"),
                    ]
                ),
            ], body=True),
        ], md=Pannel_Left),

        dbc.Col([
            dbc.Nav(
                [
                    dbc.NavLink("Data upload", href="/VolcaNoseR", active="exact"),
                    dbc.NavLink("Plot", href="/VolcaNoseR/Plot", active="exact"),
                    dbc.NavLink("About", href="/VolcaNoseR/About", active="exact"),
                ],
                pills=True, style={"background-color": "#f8f9fa"}
            ),
            html.Br(),
            dcc.Markdown(about_markdown)
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)

