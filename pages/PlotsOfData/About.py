import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import pandas as pd
from app import *

about_markdown = """
This module is a python-based implementation of the functionality of the Joachim Goedhart team’s literature. You can get more information about the setup, use, instructions and details of each function in the literature, a R language version, which is a free open-source web-based app named PlotsOfData.

PlotsOfData is available online at: [https://huygens.science.uva.nl/PlotsOfData/](https://huygens.science.uva.nl/PlotsOfData/). The source code of the current version (v1.0.5) is archived at zenodo: [https://doi.org/10.5281/zenodo.2582567](https://doi.org/10.5281/zenodo.2582567). An up-to-date version is available at Github together with information on how to install and run the app locally: [https://github.com/JoachimGoedhart/PlotsOfData](https://github.com/JoachimGoedhart/PlotsOfData).

You can read and cite the original paper from: Postma M, Goedhart J (2019) PlotsOfData—A web app for visualizing data together with their summaries. PLoS Biol 17(3): e3000202. [https://doi.org/10.1371/journal.pbio.3000202](https://doi.org/10.1371/journal.pbio.3000202).

We would like to thank Marten Postma and Joachim Goedhart that contributed the R language version, and everyone that give us advice to improve the platform.

You can contact us by email acm_ict@163.com.
"""

Layout = dbc.Container([
    LayoutHead_PlotsOfData,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("About"),
                        html.P("PSPV"),
                    ]
                ),
            ], body=True),
        ], md=Pannel_Left),

        dbc.Col([
            dbc.Nav(
                [
                    dbc.NavLink("Data upload", href="/PlotsOfData", active="exact"),
                    dbc.NavLink("Plot", href="/PlotsOfData/Plot", active="exact"),
                    dbc.NavLink("Clustering", href="/PlotTwist/Clustering", active="exact"),
                    dbc.NavLink("Data Summary", href="/PlotsOfData/DataSummary", active="exact"),
                    dbc.NavLink("About", href="/PlotsOfData/About", active="exact"),
                ],
                pills=True, style={"background-color": "#f8f9fa"}
            ),
            html.Br(),
            dcc.Markdown(about_markdown)
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)
