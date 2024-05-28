import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import pandas as pd
from app import *

about_markdown = """
This module is a python-based implementation of the functionality of the Joachim Goedhart’s literature. You can get more information about the setting, use, instructions and details of each function in the literature, a R language version, which is a free open-source web tool named PlotTwist.

PlotTwist is available online at: [https://huygens.science.uva.nl/PlotTwist](https://huygens.science.uva.nl/PlotTwist) or [https://goedhart.shinyapps.io/PlotTwist](https://goedhart.shinyapps.io/PlotTwist). The code of the version 1.0.4 is archived at Zenodo.org: [https://doi.org/10.5281/zenodo.3539121](https://doi.org/10.5281/zenodo.3539121). Up-to-date code and new releases is available on Github, together with information on running the app locally: [https://github.com/JoachimGoedhart/PlotTwist](https://github.com/JoachimGoedhart/PlotTwist).

You can read and cite the original paper from: Goedhart J (2020) PlotTwist: A web app for plotting and annotating continuous data. PLoS Biol 18(1): e3000581. [https://doi.org/10.1371/journal.pbio.3000581](https://doi.org/10.1371/journal.pbio.3000581).

We would like to thank Joachim Goedhart that contributed the R language version, and everyone that give us advice to improve the platform.

You can contact us by email acm_ict@163.com.
"""

Layout = dbc.Container([
    LayoutHead_PlotTwist,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("About"),
                        html.P("PTDV"),
                    ]
                ),
            ], body=True),
        ], md=Pannel_Left),

        dbc.Col([
            dbc.Nav(
                [
                    dbc.NavLink("Data upload", href="/PlotTwist", active="exact"),
                    dbc.NavLink("Plot", href="/PlotTwist/Plot", active="exact"),
                    dbc.NavLink("Clustering", href="/PlotTwist/Clustering", active="exact"),
                    dbc.NavLink("Data Summary", href="/PlotTwist/DataSummary", active="exact"),
                    dbc.NavLink("About", href="/PlotTwist/About", active="exact"),
                ],
                pills=True, style={"background-color": "#f8f9fa"}
            ),
            html.Br(),
            dcc.Markdown(about_markdown)
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)
