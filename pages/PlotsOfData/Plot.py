import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from app import *
import plotly.graph_objects as go

import seaborn as sns
import ptitprince as pt
import matplotlib.pyplot as plt


Layout = dbc.Container([
    dcc.Store(id='[PlotsOfData]data_input', storage_type='session'),
    dcc.Store(id='[PlotsOfData]data_tiny', storage_type='session'),  # 保存tiny信息
    LayoutHead_PlotsOfData,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("Statistics"),
                        dbc.RadioItems(
                            id="[PlotsOfData/Plot]Statistics",
                            options=[
                                {"label": "Boxplot(minimum n=10)", "value": "Box"},
                                {"label": "Violin Plot(minimum n=10)", "value": "Violin"},
                                {"label": "line chart", "value": "line"},
                                {"label": "RainCloud", "value": "RainCloud"},
                            ],
                            value="Box",
                        ),

                        html.Br(),

                        html.Strong("Plot Layout"),
                        dbc.Checklist(options=[
                            {"label": "Rotate plot 90 degrees", "value": 1},
                            # {"label": "Remove gridlines", "value": 2},
                            # {"label": "Change scale", "value": 3},
                            # {"label": "Use color for the data", "value": 4},
                            # {"label": "Use color for the stats", "value": 5},
                            # {"label": "Dark Theme", "value": 6}
                        ], value=[], id="[PlotsOfData/Plot]tran", switch=True),

                        html.Br(),

                        html.Strong("Labels/captions"),
                        dbc.Checklist(options=[
                            {"label": "Add title", "value": 1},
                        ], value=[], id="[PlotsOfData/Plot]addTitle", switch=True),
                        html.Div(id="[PlotsOfData/Plot]inputTitle", style={"width": "300px"}),
                        dcc.Store(id="[PlotsOfData/Plot]title"),
                        dbc.Checklist(options=[
                            {"label": "Change labels", "value": 1},
                        ], value=[], id="[PlotsOfData/Plot]changeLabels", switch=True),
                        html.Div(id="[PlotsOfData/Plot]inputLabels", style={"width": "300px"}),
                        dcc.Store(id="[PlotsOfData/Plot]labelValue_X"),
                        dcc.Store(id="[PlotsOfData/Plot]labelValue_Y"),

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
            html.Div([], id="[PlotsOfData/Plot]div_r", style={"width": "100%"}),
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)



# 画图
@app.callback(
    Output("[PlotsOfData/Plot]div_r", "children"),
    Input("[PlotsOfData/Plot]Statistics", "value"),
    Input("[PlotsOfData]data_input", 'data'),
    Input("[PlotsOfData/Plot]title", "children"),
    Input("[PlotsOfData/Plot]labelValue_X", "children"),
    Input("[PlotsOfData/Plot]labelValue_Y", "children"),
    Input("[PlotsOfData/Plot]tran", "value"),
    State("[PlotsOfData]data_tiny", "data"),
)
def set_plotly(statistic, data_file_content_store, title, label_x, label_y, tran, data_tiny_store):
    set_xdata = lambda x: list(x.columns)
    set_ydata = lambda y: [y[index] for index in set_xdata(y)]

    data_input_is_tiny = True
    if data_tiny_store is None:
        data_input_is_tiny = False
    elif data_tiny_store['x'] is None and data_tiny_store['y'] is None and data_tiny_store['ids'] is None and data_tiny_store['idc'] is None:
        data_input_is_tiny = False
        
    colors = ['rgba(93, 164, 214, 0.5)', 'rgba(255, 144, 14, 0.5)', 'rgba(44, 160, 101, 0.5)',
              'rgba(255, 65, 54, 0.5)', 'rgba(207, 114, 255, 0.5)', 'rgba(127, 96, 0, 0.5)']*100

    data_input = pd.read_csv(io.StringIO(data_file_content_store))
    
    if data_input_is_tiny:
        data_input = data_input.pivot_table(index=data_tiny_store['x'], columns=[data_tiny_store['idc'], data_tiny_store['ids']], values=data_tiny_store['y'])
        data_input.columns = ['_'.join( list(map(str, col)) ).replace(' ', '_') for col in data_input.columns.values]
        # data_input = data_input.reset_index()
        data_input_is_tiny = False
        
        
    fig = go.Figure()

    if tran:
        if statistic == "Box":
            for xd, yd, cls in zip(set_xdata(data_input), set_ydata(data_input), colors):
                fig.add_trace(go.Box(
                    x=yd,
                    name=xd,
                    boxpoints='all',
                    jitter=0.5,
                    whiskerwidth=0.2,
                    fillcolor=cls,
                    marker_size=4,
                    line_width=2
                ))
                fig.update_layout(
                    xaxis=dict(title=label_x, zeroline=False),
                    title=title,
                    yaxis=dict(
                        title=label_y,
                        autorange=True,
                        showgrid=True,
                        zeroline=True,
                        # dtick=10,
                        gridcolor='rgb(255, 255, 255)',
                        gridwidth=3,
                        zerolinecolor='rgb(255, 255, 255)',
                        zerolinewidth=2,
                    ),
                    margin=dict(
                        l=50,
                        r=30,
                        b=80,
                        t=100,
                    ),
                    paper_bgcolor='rgb(243, 243, 243)',
                    plot_bgcolor='rgb(243, 243, 243)',
                    showlegend=True
                )
        elif statistic == "Violin":
            for x_v, y_v in zip(set_xdata(data_input), set_ydata(data_input)):
                fig.add_trace(go.Violin(
                    x=y_v,
                    name=x_v,
                    box_visible=True,
                    line_color='black',
                    meanline_visible=True,
                    fillcolor='lightseagreen',
                    opacity=0.6
                ))

            fig.update_layout(
                dragmode="drawrect",
                title=title,
                xaxis=dict(
                    title=label_x
                ),
                yaxis=dict(
                    title=label_y,
                    autorange=True,
                    showgrid=True,
                    zeroline=True,
                    # dtick=1,
                    gridcolor='rgb(255, 255, 255)',
                    gridwidth=4,
                    zerolinecolor='rgb(255, 255, 255)',
                    zerolinewidth=2,
                ),
                margin=dict(
                    l=50,
                    r=30,
                    b=80,
                    t=100,
                ),
                paper_bgcolor='rgb(243, 243, 243)',
                plot_bgcolor='rgb(243, 243, 243)',
                showlegend=True
            )
        elif statistic == "line":
            for x_s, y_s in zip(set_xdata(data_input), set_ydata(data_input)):
                fig.add_trace(go.Scatter(
                    x=y_s,
                    name=x_s,
                    # mode='markers'
                ))
            fig.update_layout(
                dragmode="drawrect",
                title=title,
                xaxis=dict(
                    title=label_x
                ),
                yaxis=dict(
                    title=label_y,
                    autorange=True,
                    showgrid=True,
                    zeroline=True,
                    # dtick=1,
                    gridcolor='rgb(255, 255, 255)',
                    gridwidth=4,
                    zerolinecolor='rgb(255, 255, 255)',
                    zerolinewidth=2,
                ),
                margin=dict(
                    l=50,
                    r=30,
                    b=80,
                    t=100,
                ),
                paper_bgcolor='rgb(243, 243, 243)',
                plot_bgcolor='rgb(243, 243, 243)',
                showlegend=True
            )
        elif statistic == "RainCloud":
            f, ax = plt.subplots(figsize=(8, 4.5))

            pt.RainCloud(
                data=data_input,
                ax=ax,
                orient='h'
            )

            if label_x:
                ax.set_xlabel(label_x)
            if label_y:
                ax.set_ylabel(label_y)
            if title:
                ax.set_title(title)

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300)
            buf.seek(0)

            encoded_image = base64.b64encode(buf.read()).decode()
            children = [
                html.Img(src='data:image/png;base64,{}'.format(encoded_image), style={"width": "100%"})
            ]

            return children
    else:
        if statistic == "Box":
            for xd, yd, cls in zip(set_xdata(data_input), set_ydata(data_input), colors):
                fig.add_trace(go.Box(
                    y=yd,
                    name=xd,
                    boxpoints='all',
                    jitter=0.5,
                    whiskerwidth=0.2,
                    fillcolor=cls,
                    marker_size=4,
                    line_width=2)
                )
                fig.update_layout(

                    xaxis=dict(title=label_x, zeroline=False),
                    title=title,
                    yaxis=dict(
                        title=label_y,
                        autorange=True,
                        showgrid=True,
                        zeroline=True,
                        # dtick=10,
                        gridcolor='rgb(255, 255, 255)',
                        gridwidth=3,
                        zerolinecolor='rgb(255, 255, 255)',
                        zerolinewidth=2,
                    ),
                    margin=dict(
                        l=50,
                        r=30,
                        b=80,
                        t=100,
                    ),
                    paper_bgcolor='rgb(243, 243, 243)',
                    plot_bgcolor='rgb(243, 243, 243)',
                    showlegend=True
                )
        elif statistic == "Violin":
            for x_v, y_v in zip(set_xdata(data_input), set_ydata(data_input)):
                fig.add_trace(go.Violin(
                    y=y_v,
                    name=x_v,
                    box_visible=True,
                    line_color='black',
                    meanline_visible=True,
                    fillcolor='lightseagreen',
                    opacity=0.6
                ))

            fig.update_layout(
                dragmode="drawrect",
                title=title,
                xaxis=dict(
                    title=label_x
                ),
                yaxis=dict(
                    title=label_y,
                    autorange=True,
                    showgrid=True,
                    zeroline=True,
                    # dtick=1,
                    gridcolor='rgb(255, 255, 255)',
                    gridwidth=4,
                    zerolinecolor='rgb(255, 255, 255)',
                    zerolinewidth=2,
                ),
                margin=dict(
                    l=50,
                    r=30,
                    b=80,
                    t=100,
                ),
                paper_bgcolor='rgb(243, 243, 243)',
                plot_bgcolor='rgb(243, 243, 243)',
                showlegend=True
            )
        elif statistic == "line":
            for x_s, y_s in zip(set_xdata(data_input), set_ydata(data_input)):
                fig.add_trace(go.Scatter(
                    y=y_s,
                    name=x_s,
                    # mode='markers'
                ))
            fig.update_layout(
                dragmode="drawrect",
                title=title,
                xaxis=dict(
                    title=label_x
                ),
                yaxis=dict(
                    title=label_y,
                    autorange=True,
                    showgrid=True,
                    zeroline=True,
                    # dtick=1,
                    gridcolor='rgb(255, 255, 255)',
                    gridwidth=4,
                    zerolinecolor='rgb(255, 255, 255)',
                    zerolinewidth=2,
                ),
                margin=dict(
                    l=50,
                    r=30,
                    b=80,
                    t=100,
                ),
                paper_bgcolor='rgb(243, 243, 243)',
                plot_bgcolor='rgb(243, 243, 243)',
                showlegend=True
            )
        elif statistic == "RainCloud":
            f, ax = plt.subplots(figsize=(8, 4.5))

            pt.RainCloud(
                data=data_input,
                ax=ax
            )

            if label_x:
                ax.set_xlabel(label_x)
            if label_y:
                ax.set_ylabel(label_y)
            if title:
                ax.set_title(title)

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300)
            buf.seek(0)

            encoded_image = base64.b64encode(buf.read()).decode()
            children = [
                html.Img(src='data:image/png;base64,{}'.format(encoded_image), style={"width": "100%"})
            ]

            return children

    children = [
        dcc.Graph(
            id="[PlotsOfData/Plot]graph",
            config={
                "modeBarButtonsToAdd": [
                    "drawline",
                    "drawopenpath",
                    "drawclosedpath",
                    "drawcircle",
                    "drawrect",
                    "eraseshape",
                ]
            },
            figure=fig
        ),
        html.Div(id='[PlotsOfData/Plot]intermediate-value', style=dict(display=None)),
        html.Div(id='[PlotsOfData/Plot]uploadValue', style=dict(display=None))
    ]

    return children


# xy坐标标签输入框
@app.callback(
    Output("[PlotsOfData/Plot]inputLabels", "children"),
    Output("[PlotsOfData/Plot]labelValue_X", "children", allow_duplicate=True),
    Output("[PlotsOfData/Plot]labelValue_Y", "children", allow_duplicate=True),
    Input("[PlotsOfData/Plot]changeLabels", "value"),
)
def change_labels(value):
    if value:
        show = [
            html.H6("X-axis:"),
            dbc.Input(id="[PlotsOfData/Plot]input_X", placeholder="X-axis", value=''),
            html.H6("Y-axis:"),
            dbc.Input(id="[PlotsOfData/Plot]input_Y", placeholder="Y-axis", value='')
        ]
    else:
        show = []
    return show, None, None


# x坐标标签
@app.callback(
    Output("[PlotsOfData/Plot]labelValue_X", "children", allow_duplicate=True),
    Input("[PlotsOfData/Plot]input_X", "value")
)
def label_value(value):
    if value == None:
        value = ''

    return value


# y坐标标签
@app.callback(
    Output("[PlotsOfData/Plot]labelValue_Y", "children", allow_duplicate=True),
    Input("[PlotsOfData/Plot]input_Y", "value")
)
def label_value_y(value):
    if value == None:
        value = ''
    return value


# 标题输入框
@app.callback(
    Output("[PlotsOfData/Plot]inputTitle", "children"),
    Output("[PlotsOfData/Plot]title", "children", allow_duplicate=True),
    Input("[PlotsOfData/Plot]addTitle", "value")
)
def add_title(value):
    if value:
        show = [
            dbc.Input(id="[PlotsOfData/Plot]inputtitle", placeholder="Title")
        ]
    else:
        show = []
    return show, None


# 标题
@app.callback(
    Output("[PlotsOfData/Plot]title", "children", allow_duplicate=True),
    Input("[PlotsOfData/Plot]inputtitle", "value")
)
def title(value):
    return value
