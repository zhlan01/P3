import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from app import *

Layout = dbc.Container([
    dcc.Store(id='[VolcaNoseR]data_input', storage_type='session'),
    dcc.Store(id='[VolcaNoseR]data_tiny', storage_type='session'),  # 保存tiny信息
    dcc.Store(id='[VolcaNoseR/VolcaNoseR]open_time', data=0),
    LayoutHead_VolcaNoseR,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("Data upload"),
                        dbc.RadioItems(
                            id="[VolcaNoseR/VolcaNoseR]data_input_type",
                            options=[
                                {"label": "Example data 1", "value": "data1"},
                                {"label": "Example data 2", "value": "data2"},
                                {"label": "Upload file", "value": "load_mul"},
                            ],
                            value="data1",
                        ),
                        html.Div(id="[VolcaNoseR/VolcaNoseR]file_upload"),

                        html.Br(),

                        html.Div(id="[VolcaNoseR/VolcaNoseR]tiny_info"),

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
            html.Div(id="[VolcaNoseR/VolcaNoseR]div_r", style={"width": "100%"}),
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)


# 处理右侧表格
@app.callback(
    Output("[VolcaNoseR/VolcaNoseR]div_r", "children"),
    Output("[VolcaNoseR]data_input", "data", allow_duplicate=True),
    Output("[VolcaNoseR/VolcaNoseR]open_time", "data"),
    Output("[VolcaNoseR/VolcaNoseR]data_input_type", "value", allow_duplicate=True),
    Output("[VolcaNoseR]data_tiny", "data"),
    Input("[VolcaNoseR/VolcaNoseR]data_input_type", "value"),
    State("[VolcaNoseR]data_input", "data"),
    Input("[VolcaNoseR/VolcaNoseR]open_time", "data"),
    State("[VolcaNoseR]data_tiny", "data"),
)
def set_table_data(data_input_type, data_file_content_store, open_time, data_tiny_store):
    if open_time == 0 and data_file_content_store != None:
        data_file_content = data_file_content_store
        data_input_type = "load_mul"

    else:
        if data_input_type == "data1":
            data_file_content = open("Example/Becares-diffgenes_HFHC.csv").read()
            data_tiny_store = {"x": "log2_FoldChange", "y": "minus_log10_pvalue", "idn": "Gene"}
        elif data_input_type == "data2":
            data_file_content = open("Example/elife-45916-Cdc42QL_data.csv").read()
            data_tiny_store = {"x": "log2_FoldChange", "y": "minus_log10_pvalue", "idn": "Gene"}
        elif data_input_type == "load_mul":
            data_file_content = data_file_content_store
            data_tiny_store = {"x": None, "y": None, "idn": None}


    data_input = pd.read_csv(io.StringIO(data_file_content))

    table = [
        dash_table.DataTable(
            id='[VolcaNoseR/VolcaNoseR]table',
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
    return table, data_file_content, open_time + 1, data_input_type, data_tiny_store


# tiny输入框
@app.callback(
    Output("[VolcaNoseR/VolcaNoseR]tiny_info", "children"),
    Output("[VolcaNoseR]data_tiny", "data", allow_duplicate=True),
    Input("[VolcaNoseR/VolcaNoseR]data_input_type", "value"),
    State("[VolcaNoseR]data_input", "data"),
    State("[VolcaNoseR]data_tiny", "data"),
)
def input_tiny_info(data_input_type, data_file_content_store, data_tiny_store):

    if data_file_content_store == None:
        return [], data_tiny_store

    data_input = pd.read_csv(io.StringIO(data_file_content_store))
    data_input_head = []
    for i in list(data_input.columns):
        if not i.startswith("Unnamed:"):
            data_input_head.append(i)

    show = [
        html.Strong("Select X & Y variables"),
        html.Br(),
        html.A("X-axis; Effect (fold change)"),
        dbc.Select(
            id="[VolcaNoseR/VolcaNoseR]tiny_info_x",
            options=[{"label": "None", "value": "None"}] + [
                {"label": i, "value": i} for i in data_input_head
            ],
            value="None" if data_tiny_store['x'] == None else data_tiny_store['x']
        ),

        html.A("Y-axis; Significance (p-value)"),
        dbc.Select(
            id="[VolcaNoseR/VolcaNoseR]tiny_info_y",
            options=[{"label": "None", "value": "None"}] + [
                {"label": i, "value": i} for i in data_input_head
            ],
            value="None" if data_tiny_store['y'] == None else data_tiny_store['y']
        ),

        html.A("Select column with names"),
        dbc.Select(
            id="[VolcaNoseR/VolcaNoseR]tiny_info_idn",
            options=[{"label": "None", "value": "None"}] + [
                {"label": i, "value": i} for i in data_input_head
            ],
            value="None" if data_tiny_store['idn'] == None else data_tiny_store['idn']
        ),
    ]

    return show, data_tiny_store


# 处理上传文件按钮
@app.callback(Output("[VolcaNoseR/VolcaNoseR]file_upload", "children"),
              Input("[VolcaNoseR/VolcaNoseR]data_input_type", "value"))
def get_load(value):
    if value != "load_mul":
        return
    show = [
        dcc.Upload(
            id='[VolcaNoseR/VolcaNoseR]datatable-upload',
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
    Output("[VolcaNoseR]data_input", "data", allow_duplicate=True),
    Output("[VolcaNoseR/VolcaNoseR]data_input_type", "value", allow_duplicate=True),
    Input('[VolcaNoseR/VolcaNoseR]datatable-upload', 'contents'),
    State('[VolcaNoseR]data_input', 'data'),
)
def update_output(contents, data_file_content_store):
    if contents == None:
        return data_file_content_store, "load_mul"

    contents = base64.b64decode(contents.split(',')[1]).decode("utf-8")
    data_input = pd.read_csv(io.StringIO(contents))
    return contents, "load_mul"

# tiny
@app.callback(
    Output("[VolcaNoseR]data_tiny", "data", allow_duplicate=True),
    State("[VolcaNoseR]data_tiny", "data"),
    Input("[VolcaNoseR/VolcaNoseR]tiny_info_x", "value"),
    Input("[VolcaNoseR/VolcaNoseR]tiny_info_y", "value"),
    Input("[VolcaNoseR/VolcaNoseR]tiny_info_idn", "value"),
)
def save_tiny_info(data_tiny_store, x, y, idn):
    if data_tiny_store == None:
        data_tiny_store = {"x": None, "y": None, "idn": None}

    data_tiny_store['x'] = None if x == "None" else x
    data_tiny_store['y'] = None if y == "None" else y
    data_tiny_store['idn'] = None if idn == "None" else idn


    return data_tiny_store
