import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from app import *

Layout = dbc.Container([
    dcc.Store(id='[PlotsTwist]data_input', storage_type='session'),
    dcc.Store(id='[PlotsTwist]data_tiny', storage_type='session'),  # 保存tiny信息
    dcc.Store(id='[PlotsTwist/PlotsTwist]open_time', data=0),
    LayoutHead_PlotTwist,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("Data upload (First column used for x-axis)"),
                        dbc.RadioItems(
                            id="[PlotsTwist/PlotsTwist]data_input_type",
                            options=[
                                {"label": "Example 1 (wide format)", "value": "wide_fm"},
                                {"label": "Example 2 (tidy format)", "value": "tidy_fm"},
                                {"label": "Upload file", "value": "load_mul"},
                            ],
                            value="wide_fm",
                        ),
                        html.Div(id="[PlotsTwist/PlotsTwist]file_upload"),

                        html.Br(),

                        dbc.Checklist(
                            id="[PlotsTwist/PlotsTwist]data_input_istiny",
                            options=[
                                {"label": "These data are Tidy", "value": "istiny"},
                            ]
                        ),
                        html.Div(id="[PlotsTwist/PlotsTwist]tiny_info"),

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
            html.Div(id="[PlotsTwist/PlotsTwist]div_r", style={"width": "100%"}),
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)


# 处理右侧表格
@app.callback(
    Output("[PlotsTwist/PlotsTwist]div_r", "children"),
    Output("[PlotsTwist]data_input", "data", allow_duplicate=True),
    Output("[PlotsTwist/PlotsTwist]open_time", "data"),
    Output("[PlotsTwist/PlotsTwist]data_input_type", "value", allow_duplicate=True),
    Output("[PlotsTwist/PlotsTwist]data_input_istiny", "value"),
    Output("[PlotsTwist]data_tiny", "data"),
    Input("[PlotsTwist/PlotsTwist]data_input_type", "value"),
    State("[PlotsTwist]data_input", "data"),
    Input("[PlotsTwist/PlotsTwist]open_time", "data"),
    State("[PlotsTwist]data_tiny", "data"),
)
def set_table_data(data_input_type, data_file_content_store, open_time, data_tiny_store):
    is_tiny = dash.no_update

    if open_time == 0 and data_file_content_store != None:
        data_file_content = data_file_content_store
        data_input_type = "load_mul"

        is_tiny = ['istiny']
        if data_tiny_store is None:
            is_tiny = []
        elif data_tiny_store['x'] is None and data_tiny_store['y'] is None and data_tiny_store['ids'] is None and data_tiny_store['idc'] is None:
            is_tiny = []


    else:
        is_tiny = []
        if data_input_type == "wide_fm":
            data_file_content = open("Example/Data_wide_example_time_single.csv").read()
        elif data_input_type == "tidy_fm":
            data_file_content = open("Example/Data_tidy_example_time_multi.csv").read()
            is_tiny = ['istiny']
            data_tiny_store = {"x": "Time", "y": "Value", "ids": "Sample", "idc": "id"}
        elif data_input_type == "load_mul":
            data_file_content = data_file_content_store


    data_input = pd.read_csv(io.StringIO(data_file_content))

    table = [
        dash_table.DataTable(
            id='[PlotsTwist/PlotsTwist]table',
            data=data_input.to_dict('records'),
            columns=[
                {'name': i, 'id': i, 'deletable': False} for i in data_input.columns
            ],
            page_size=15,
            sort_action='native',
            sort_mode='single',
            style_cell_conditional=[
                {
                    'if': {'column_id': c},
                    'textAlign': 'left'
                } for c in ['Date', 'Region']
            ],
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            export_format='csv'
        )]
    return table, data_file_content, open_time + 1, data_input_type, is_tiny, data_tiny_store


# 处理上传文件按钮
@app.callback(Output("[PlotsTwist/PlotsTwist]file_upload", "children"),
              Input("[PlotsTwist/PlotsTwist]data_input_type", "value"))
def get_load(value):
    if value != "load_mul":
        return
    show = [
        dcc.Upload(
            id='[PlotsTwist/PlotsTwist]datatable-upload',
            children=html.Div([
                'Drag and Drop or Select Files',
            ]),
            style={
                'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
            },
        )
    ]
    return show


# 上传文件判断可用性后保存至data_input
@app.callback(
    Output("[PlotsTwist]data_input", "data", allow_duplicate=True),
    Output("[PlotsTwist/PlotsTwist]data_input_type", "value", allow_duplicate=True),
    Input('[PlotsTwist/PlotsTwist]datatable-upload', 'contents'),
    State('[PlotsTwist]data_input', 'data'),
)
def update_output(contents, data_file_content_store):
    if contents == None:
        return data_file_content_store, "load_mul"

    contents = base64.b64decode(contents.split(',')[1]).decode("utf-8")
    data_input = pd.read_csv(io.StringIO(contents))
    return contents, "load_mul"


# tiny输入框
@app.callback(
    Output("[PlotsTwist/PlotsTwist]tiny_info", "children"),
    Output("[PlotsTwist]data_tiny", "data", allow_duplicate=True),
    Input("[PlotsTwist/PlotsTwist]data_input_istiny", "value"),
    State("[PlotsTwist]data_input", "data"),
    State("[PlotsTwist]data_tiny", "data"),
)
def input_tiny_info(value, data_file_content_store, data_tiny_store):

    if data_file_content_store == None:
        return [], data_tiny_store

    data_input = pd.read_csv(io.StringIO(data_file_content_store))
    data_input_head = []
    for i in list(data_input.columns):
        if not i.startswith("Unnamed:"):
            data_input_head.append(i)

    if value:
        show = [
            html.Strong("Select variable for x-axis"),
            dbc.Select(
                id="[PlotsTwist/PlotsTwist]tiny_info_x",
                options=[{"label": "None", "value": "None"}] + [
                    {"label": i, "value": i} for i in data_input_head
                ],
                value="None" if data_tiny_store['x'] == None else data_tiny_store['x']
            ),

            html.Strong("Select variable for y-axis"),
            dbc.Select(
                id="[PlotsTwist/PlotsTwist]tiny_info_y",
                options=[{"label": "None", "value": "None"}] + [
                    {"label": i, "value": i} for i in data_input_head
                ],
                value="None" if data_tiny_store['y'] == None else data_tiny_store['y']
            ),

            html.Strong("Identifier of samples"),
            dbc.Select(
                id="[PlotsTwist/PlotsTwist]tiny_info_ids",
                options=[{"label": "None", "value": "None"}] + [
                    {"label": i, "value": i} for i in data_input_head
                ],
                value="None" if data_tiny_store['ids'] == None else data_tiny_store['ids']
            ),

            html.Strong("Identifier of conditions"),
            dbc.Select(
                id="[PlotsTwist/PlotsTwist]tiny_info_idc",
                options=[{"label": "None", "value": "None"}] + [
                    {"label": i, "value": i} for i in data_input_head
                ],
                value="None" if data_tiny_store['idc'] == None else data_tiny_store['idc']
            ),

        ]
    else:
        show = []
        data_tiny_store = {"x": None, "y": None, "ids": None, "idc": None}
    return show, data_tiny_store


# tiny
@app.callback(
    Output("[PlotsTwist]data_tiny", "data", allow_duplicate=True),
    State("[PlotsTwist]data_tiny", "data"),
    Input("[PlotsTwist/PlotsTwist]tiny_info_x", "value"),
    Input("[PlotsTwist/PlotsTwist]tiny_info_y", "value"),
    Input("[PlotsTwist/PlotsTwist]tiny_info_ids", "value"),
    Input("[PlotsTwist/PlotsTwist]tiny_info_idc", "value"),
)
def save_tiny_info(data_tiny_store, x, y, ids, idc):
    if data_tiny_store == None:
        data_tiny_store = {"x": None, "y": None, "ids": None, "idc": None}

    data_tiny_store['x'] = None if x == "None" else x
    data_tiny_store['y'] = None if y == "None" else y
    data_tiny_store['ids'] = None if ids == "None" else ids
    data_tiny_store['idc'] = None if idc == "None" else idc


    return data_tiny_store
