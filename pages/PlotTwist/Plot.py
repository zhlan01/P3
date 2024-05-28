import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from app import *
import plotly.graph_objects as go
import plotly.express as px

Layout = dbc.Container([
    dcc.Store(id='[PlotsTwist]data_input', storage_type='session'),
    dcc.Store(id='[PlotsTwist]data_tiny', storage_type='session'),  # 保存tiny信息
    LayoutHead_PlotTwist,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("Data as:"),
                        dbc.RadioItems(
                            id="[PlotsTwist/Plot]data_as",
                            options=[
                                {"label": "Lines", "value": "line"},
                                {"label": "Dots", "value": "dot"},
                                {"label": "Heatmap", "value": "heatmap"},
                                {"label": "Marginal Distribution", "value": "MD"}
                            ],
                            value="line"
                        ),

                        html.Br(),

                        html.Strong("Labels/captions"),
                        dbc.Checklist(options=[
                            {"label": "Add title", "value": 1},
                        ], value=[], id="[PlotsTwist/Plot]addTitle", switch=True),
                        html.Div(id="[PlotsTwist/Plot]inputTitle", style={"width": "300px"}),
                        dcc.Store(id="[PlotsTwist/Plot]title"),
                        dbc.Checklist(options=[
                            {"label": "Change labels", "value": 1},
                        ], value=[], id="[PlotsTwist/Plot]changeLabels", switch=True),
                        html.Div(id="[PlotsTwist/Plot]inputLabels", style={"width": "300px"}),
                        dcc.Store(id="[PlotsTwist/Plot]labelValue_X"),
                        dcc.Store(id="[PlotsTwist/Plot]labelValue_Y"),

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
                dcc.Graph(id="[PlotsTwist/Plot]graph"),
                html.Div(id='[PlotsTwist/Plot]intermediate-value_pt', style=dict(display=None)),
                html.Div(id='[PlotsTwist/Plot]intermediate-value_pt_hot', style=dict(display=None)),
                html.Div(id='[PlotsTwist/Plot]uploadValue_pt', style=dict(display=None))
            ], id="[PlotsTwist/Plot]div_r", style={"width": "100%"}),
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)


# 画图
@app.callback(
    Output("[PlotsTwist/Plot]graph", "figure"),
    Input("[PlotsTwist/Plot]data_as", "value"),
    Input("[PlotsTwist]data_input", 'data'),
    Input("[PlotsTwist/Plot]title", "children"),
    Input("[PlotsTwist/Plot]labelValue_X", "children"),
    Input("[PlotsTwist/Plot]labelValue_Y", "children"),
    State("[PlotsTwist]data_tiny", "data"),
)
def set_plotly(data_as, data_file_content_store, title, label_x, label_y, data_tiny_store):
    set_xdata = lambda x: list(x.columns)
    set_ydata = lambda y: [y[index] for index in set_xdata(y)]

    data_input_is_tiny = True
    if data_tiny_store is None:
        data_input_is_tiny = False
    elif data_tiny_store['x'] is None and data_tiny_store['y'] is None and data_tiny_store['ids'] is None and data_tiny_store['idc'] is None:
        data_input_is_tiny = False
    
    data_input = pd.read_csv(io.StringIO(data_file_content_store))
    
    if data_input_is_tiny:
        data_input = data_input.pivot_table(index=data_tiny_store['x'], columns=[data_tiny_store['idc'], data_tiny_store['ids']], values=data_tiny_store['y'])
        data_input.columns = ['_'.join( list(map(str, col)) ).replace(' ', '_') for col in data_input.columns.values]
        data_input = data_input.reset_index()
        data_input_is_tiny = False
    
    if data_as == "line":
        fig = go.Figure()

        for x_s, y_s in zip(set_xdata(data_input)[1:], set_ydata(data_input)[1:]):
            fig.add_trace(go.Scatter(
                y=y_s,
                name=x_s,
                # mode='markers'
            ))

        fig.update_layout(
            title=title,
            xaxis=dict(title=label_x, zeroline=False),
            yaxis_title=label_y,
        )
    elif data_as == "dot":
        fig = go.Figure()
        fig.update_layout(
            title=title,
            yaxis_title=label_y,
            xaxis_title=label_x,
            yaxis=dict(
                autorange=True,
                showgrid=True,
                zeroline=True,
                # dtick=1,
                gridcolor='rgb(255, 255, 255)',
                gridwidth=1,
                zerolinecolor='rgb(255, 255, 255)',
                zerolinewidth=4,
            ),
            margin=dict(
                l=50,
                r=30,
                b=80,
                t=100,
            ),
            paper_bgcolor='rgb(243, 243, 243)',
            plot_bgcolor='rgb(243, 243, 243)',
            showlegend=True,
        )
        for x_s, y_s in zip(set_xdata(data_input)[1:], set_ydata(data_input)[1:]):
            fig.add_trace(go.Scatter(
                y=y_s,
                name=x_s,
                mode='markers'
            ))

    elif data_as == "heatmap":
        data = []
        data.append(list(data_input.columns))
        for i in data_input.index:
            data.append(list(data_input.values[i]))
        allnodes = data  # 若想用二维列表的形式读取即删掉此行语句
        all1 = []
        for i in range(len(allnodes)):
            all1.append(allnodes[i][1:])
        all2 = []
        for i in range(len(allnodes)):
            all2.append(allnodes[i][0])

        fig = go.Figure(data=go.Heatmap(
            z=all1[1:],
            x=allnodes[0][1:],
            y=all2[1:],
            hoverongaps=False,
            colorscale='Viridis'))
                
        fig.update_layout(
            title=title,
            xaxis=dict(title=label_x, zeroline=False),
            yaxis_title=label_y,
        )

    elif data_as == "MD":
        fig = px.histogram(data_input.iloc[:, 1:], marginal="rug")
        
        fig.update_layout(
            title=title,
            yaxis_title=label_y,
            xaxis_title=label_x,
        )
    return fig


# xy坐标标签输入框
@app.callback(
    Output("[PlotsTwist/Plot]inputLabels", "children"),
    Output("[PlotsTwist/Plot]labelValue_X", "children", allow_duplicate=True),
    Output("[PlotsTwist/Plot]labelValue_Y", "children", allow_duplicate=True),
    Input("[PlotsTwist/Plot]changeLabels", "value"),
)
def change_labels(value):
    if value:
        show = [
            html.H6("X-axis:"),
            dbc.Input(id="[PlotsTwist/Plot]input_X", placeholder="X-axis", value=''),
            html.H6("Y-axis:"),
            dbc.Input(id="[PlotsTwist/Plot]input_Y", placeholder="Y-axis", value='')
        ]
    else:
        show = []
    return show, None, None


# x坐标标签
@app.callback(
    Output("[PlotsTwist/Plot]labelValue_X", "children", allow_duplicate=True),
    Input("[PlotsTwist/Plot]input_X", "value")
)
def label_value(value):
    if value == None:
        value = ''

    return value


# y坐标标签
@app.callback(
    Output("[PlotsTwist/Plot]labelValue_Y", "children", allow_duplicate=True),
    Input("[PlotsTwist/Plot]input_Y", "value")
)
def label_value_y(value):
    if value == None:
        value = ''
    return value


# 标题输入框
@app.callback(
    Output("[PlotsTwist/Plot]inputTitle", "children"),
    Output("[PlotsTwist/Plot]title", "children", allow_duplicate=True),
    Input("[PlotsTwist/Plot]addTitle", "value")
)
def add_title(value):
    if value:
        show = [
            dbc.Input(id="[PlotsTwist/Plot]inputtitle", placeholder="Title")
        ]
    else:
        show = []
    return show, None


# 标题
@app.callback(
    Output("[PlotsTwist/Plot]title", "children", allow_duplicate=True),
    Input("[PlotsTwist/Plot]inputtitle", "value")
)
def title(value):
    return value
