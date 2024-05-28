import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from app import *
from scipy import stats
import numpy as np

statistics_for_table = ['mean', 'sd', 'sem', '95CI mean', 'median', 'MAD', 'IQR', 'Q1', 'Q3', '95CI median']

Layout = dbc.Container([
    dcc.Store(id='[PlotsTwist]data_input', storage_type='session'),
    dcc.Store(id='[PlotsTwist]data_tiny', storage_type='session'),  # 保存tiny信息
    dcc.Store(id='[PlotsTwist/DataSummary]open_time', data=0),
    LayoutHead_PlotTwist,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("Statistics for table:"),
                        dbc.Checklist(
                            id="[PlotsTwist/DataSummary]check_show",
                            options=[{"label": i, "value": i} for i in statistics_for_table],
                            value=["mean", "median", "sd", "sem", "95CI mean"]
                        ),

                        html.Br(),

                        html.Strong("Digits:"),
                        dbc.Input(id="[PlotsTwist/DataSummary]digits", value=2),

                        #
                        # html.Strong("Normalization"),
                        # dbc.Checklist(id='[PlotsTwist/DataSummary]DNormalization', options=[
                        #     {"label": "Data normalization", "value": 1}
                        # ]),
                        # html.Hr(),
                        # dbc.Checklist(id='[PlotsTwist/DataSummary]ShowInformation', options=[
                        #     {"label": "Show information on data formats", "value": 1}
                        # ]),
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
            html.Div([
                dash_table.DataTable(
                    id="[PlotsTwist/DataSummary]show_data",
                    style_data={'textAlign': 'center'},
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                    },
                    export_format='csv'
                )
            ]),
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)


@app.callback(
    Output("[PlotsTwist/DataSummary]show_data", "columns"),
    Output("[PlotsTwist/DataSummary]show_data", "data"),
    Input("[PlotsTwist/DataSummary]check_show", "value"),
    State("[PlotsTwist]data_input", "data"),
    Input("[PlotsTwist/DataSummary]digits", "value"),
    State("[PlotsTwist]data_tiny", "data"),
)
def change_data(value, data_file_content_store, digits_store, data_tiny_store):
    data_input_is_tiny = True
    if data_tiny_store is None:
        data_input_is_tiny = False
    elif data_tiny_store['x'] is None and data_tiny_store['y'] is None and data_tiny_store['ids'] is None and data_tiny_store['idc'] is None:
        data_input_is_tiny = False
    
    if not digits_store:
        digits_store = 2
    else:
        digits_store = int(digits_store)
        
    # print(data_tiny_store)
    data_input = pd.read_csv(io.StringIO(data_file_content_store), index_col=0)
    
    if data_input_is_tiny:
        data_input = data_input.pivot_table(index=data_tiny_store['x'], columns=[data_tiny_store['idc'], data_tiny_store['ids']], values=data_tiny_store['y'])
        data_input.columns = ['_'.join( list(map(str, col)) ).replace(' ', '_') for col in data_input.columns.values]
        # data_input = data_input.reset_index()
        data_input_is_tiny = False
        
    data_input = data_input.T
    condition_name = str(data_input.columns.name)

    data_input_Condition = list(data_input.columns)
    data_input_n = data_input.count()
    data_input_mean = data_input.mean(numeric_only=True)

    data_input_sd = data_input.std(numeric_only=True)
    data_input_sem = data_input.sem(numeric_only=True)
    data_input_median = data_input.median(numeric_only=True)
    data_input_MAD = data_input.mad()
    data_input_Q1 = data_input.quantile(q=0.25)
    data_input_Q3 = data_input.quantile(q=0.75)
    data_input_IQR = data_input_Q3 - data_input_Q1

    # 对于均值
    data_input_95CI_mean = stats.t.interval(
        alpha=0.95,
        df=data_input_n - 1,
        loc=data_input_mean,
        scale=data_input_sem
    )

    # 对于中位数
    data_input_95CI_median = stats.t.interval(
        alpha=0.95,
        df=data_input_n - 1,
        loc=data_input_median,
        scale=(data_input_sd / np.sqrt(data_input_n))
    )

    columns = [{"name": i, "id": i} for i in [condition_name, "n"]]

    for i in statistics_for_table:
        if i in value:
            columns.append({"name": i, "id": i})

    data = [
        {
            condition_name: _Condition,
            'n': _n,
            'median': round(_median, digits_store),
            'MAD': round(_MAD, digits_store),
            'IQR': round(_IQR, digits_store),
            "Q1": round(_Q1, digits_store),
            "Q3": round(_Q3, digits_store),
            'mean': round(_mean, digits_store),
            'sem': round(_sem, digits_store),
            'sd': round(_sd, digits_store),
            '95CI mean': f"{round(_95CI_mean_low, digits_store)} - {round(_95CI_mean_high, digits_store)}",
            '95CI median': f"{round(_95CI_median_low, digits_store)} - {round(_95CI_median_high, digits_store)}",
        } for _Condition, _n, _median, _MAD, _IQR, _Q1, _Q3, _mean, _sem, _sd, _95CI_mean_low, _95CI_mean_high, _95CI_median_low, _95CI_median_high in zip(
            data_input_Condition,
            data_input_n,
            data_input_median,
            data_input_MAD,
            data_input_IQR,
            data_input_Q1,
            data_input_Q3,
            data_input_mean,
            data_input_sem,
            data_input_sd,
            data_input_95CI_mean[0],
            data_input_95CI_mean[1],
            data_input_95CI_median[0],
            data_input_95CI_median[1]
        )
    ]
    return columns, data
