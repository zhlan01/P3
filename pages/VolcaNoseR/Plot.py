import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from app import *
import plotly.graph_objects as go
import plotly.express as px

Layout = dbc.Container([
    dcc.Store(id='[VolcaNoseR]data_input', storage_type='session'),
    dcc.Store(id='[VolcaNoseR]data_tiny', storage_type='session'),  # 保存tiny信息
    LayoutHead_VolcaNoseR,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Label("Fold change threshold:"),
                        dcc.RangeSlider(
                            -5, 5,
                            value=[-1.5, 1.5],
                            id='[PlotsTwist/Clustering]threshold_x',
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),

                        html.Br(),

                        html.Label("Significance threshold:"),
                        dcc.Slider(
                            0, 5,
                            value=2,
                            id='[PlotsTwist/Clustering]threshold_y',
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),

                        html.Br(),

                        html.Strong("Labels/captions"),
                        dbc.Checklist(options=[
                            {"label": "Add title", "value": 1},
                        ], value=[], id="[VolcaNoseR/Plot]addTitle", switch=True),
                        html.Div(id="[VolcaNoseR/Plot]inputTitle", style={"width": "300px"}),
                        dcc.Store(id="[VolcaNoseR/Plot]title"),
                        dbc.Checklist(options=[
                            {"label": "Change labels", "value": 1},
                        ], value=[], id="[VolcaNoseR/Plot]changeLabels", switch=True),
                        html.Div(id="[VolcaNoseR/Plot]inputLabels", style={"width": "300px"}),
                        dcc.Store(id="[VolcaNoseR/Plot]labelValue_X"),
                        dcc.Store(id="[VolcaNoseR/Plot]labelValue_Y"),

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
            html.Div([
                dcc.Graph(id="[VolcaNoseR/Plot]graph"),
                html.Div(id='[VolcaNoseR/Plot]intermediate-value_pt', style=dict(display=None)),
                html.Div(id='[VolcaNoseR/Plot]intermediate-value_pt_hot', style=dict(display=None)),
                html.Div(id='[VolcaNoseR/Plot]uploadValue_pt', style=dict(display=None))
            ], id="[VolcaNoseR/Plot]div_r", style={"width": "100%"}),
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)


# 画图
@app.callback(
    Output("[VolcaNoseR/Plot]graph", "figure"),
    Input("[VolcaNoseR]data_input", 'data'),
    Input("[VolcaNoseR/Plot]title", "children"),
    Input("[VolcaNoseR/Plot]labelValue_X", "children"),
    Input("[VolcaNoseR/Plot]labelValue_Y", "children"),
    State("[VolcaNoseR]data_tiny", "data"),
    Input("[PlotsTwist/Clustering]threshold_x", "value"),
    Input("[PlotsTwist/Clustering]threshold_y", "value"),
)
def set_plotly(data_file_content_store, title, label_x, label_y, data_tiny_store, threshold_x, threshold_y):
    if label_x == None:
        label_x = 'Fold change (Log2)'
    if label_y == None:
        label_y = 'Significance (-Log10)'
    set_xdata = lambda x: list(x.columns)
    set_ydata = lambda y: [y[index] for index in set_xdata(y)]

    data_input = pd.read_csv(io.StringIO(data_file_content_store))

    fig = go.Figure()

    fig.update_layout(
        title=title,
        yaxis_title=label_y,
        xaxis_title=label_x,
    )

    # fig.add_trace(go.Scatter(
    #     x=data_input[data_tiny_store['x']],
    #     y=data_input[data_tiny_store['y']],
    #     text=data_input[data_tiny_store['idn']],
    #     mode="markers"
    # ))
    result = pd.DataFrame()
    result['x'] = data_input[data_tiny_store['x']]
    result['y'] = data_input[data_tiny_store['y']]
    result['text'] = data_input[data_tiny_store['idn']]

    # 确定坐标轴显示范围
    xmax = max(data_input[data_tiny_store['x']]) * 1.1
    xmin = min(data_input[data_tiny_store['x']]) * 1.1
    ymin = 0
    ymax = max(data_input[data_tiny_store['y']]) * 1.1

    # 分组为up, normal, down
    result['group'] = 'black'
    result.loc[(result.x > threshold_x[1]) & (result.y > threshold_y), 'group'] = 'red'  # x=-+x_threshold直接截断
    result.loc[(result.x < threshold_x[0]) & (result.y > threshold_y), 'group'] = 'blue'  # x=-+x_threshold直接截断
    result.loc[result.y < threshold_y, 'group'] = 'dimgrey'  # 阈值以下点为灰色

    result['mode'] = 'markers'
    result.loc[(result.x > threshold_x[1]) & (result.y > threshold_y), 'mode'] = 'markers+text'  # x=-+x_threshold直接截断
    result.loc[(result.x < threshold_x[0]) & (result.y > threshold_y), 'mode'] = 'markers+text'  # x=-+x_threshold直接截断

    # 分别创建 'marker' 和 'marker+text' 的 Scatter
    scatter_marker = go.Scatter(
        x=result[result['mode'] == 'markers']['x'],
        y=result[result['mode'] == 'markers']['y'],
        mode='markers',
        marker=dict(
            size=10,
            opacity=0.5,
            color=result[result['mode'] == 'markers']['group']
        )
    )

    scatter_marker_text = go.Scatter(
        x=result[result['mode'] == 'markers+text']['x'],
        y=result[result['mode'] == 'markers+text']['y'],
        text=result[result['mode'] == 'markers+text']['text'],
        mode='markers+text',
        textposition="top center",
        marker=dict(
            size=10,
            opacity=0.5,
            color=result[result['mode'] == 'markers+text']['group']
        )
    )

    # 添加到图中
    fig.add_trace(scatter_marker)
    fig.add_trace(scatter_marker_text)

    # Set layout for the figure
    fig.update_xaxes(range=[xmin, xmax])
    fig.update_yaxes(range=[ymin, ymax])

    # Add vertical and horizontal lines
    fig.add_shape(dict(type="line", x0=threshold_x[0], x1=threshold_x[0], y0=ymin, y1=ymax, line=dict(color='dimgrey', dash='dash')))
    fig.add_shape(dict(type="line", x0=threshold_x[1], x1=threshold_x[1], y0=ymin, y1=ymax, line=dict(color='dimgrey', dash='dash')))
    fig.add_shape(dict(type="line", x0=xmin, x1=xmax, y0=threshold_y, y1=threshold_y, line=dict(color='dimgrey', dash='dash')))

    # Update the x and y axis ticks
    fig.update_xaxes(tickvals=list(range(-8, 12, 2)))
    fig.update_yaxes(tickvals=list(range(-20, 380, 40)))

    fig.update_layout(
        margin=dict(l=50, r=50, t=30, b=20),  # 设置上下左右边距为50像素
        height=600
    )

    return fig


# xy坐标标签输入框
@app.callback(
    Output("[VolcaNoseR/Plot]inputLabels", "children"),
    Output("[VolcaNoseR/Plot]labelValue_X", "children", allow_duplicate=True),
    Output("[VolcaNoseR/Plot]labelValue_Y", "children", allow_duplicate=True),
    Input("[VolcaNoseR/Plot]changeLabels", "value"),
)
def change_labels(value):
    if value:
        show = [
            html.H6("X-axis:"),
            dbc.Input(id="[VolcaNoseR/Plot]input_X", placeholder="X-axis", value=''),
            html.H6("Y-axis:"),
            dbc.Input(id="[VolcaNoseR/Plot]input_Y", placeholder="Y-axis", value='')
        ]
    else:
        show = []
    return show, None, None


# x坐标标签
@app.callback(
    Output("[VolcaNoseR/Plot]labelValue_X", "children", allow_duplicate=True),
    Input("[VolcaNoseR/Plot]input_X", "value")
)
def label_value(value):
    if value == None:
        value = ''

    return value


# y坐标标签
@app.callback(
    Output("[VolcaNoseR/Plot]labelValue_Y", "children", allow_duplicate=True),
    Input("[VolcaNoseR/Plot]input_Y", "value")
)
def label_value_y(value):
    if value == None:
        value = ''
    return value


# 标题输入框
@app.callback(
    Output("[VolcaNoseR/Plot]inputTitle", "children"),
    Output("[VolcaNoseR/Plot]title", "children", allow_duplicate=True),
    Input("[VolcaNoseR/Plot]addTitle", "value")
)
def add_title(value):
    if value:
        show = [
            dbc.Input(id="[VolcaNoseR/Plot]inputtitle", placeholder="Title")
        ]
    else:
        show = []
    return show, None


# 标题
@app.callback(
    Output("[VolcaNoseR/Plot]title", "children", allow_duplicate=True),
    Input("[VolcaNoseR/Plot]inputtitle", "value")
)
def title(value):
    return value
