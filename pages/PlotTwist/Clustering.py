import base64, io, json
from dash.dependencies import Output, Input, State
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from app import *
import plotly.graph_objects as go

from sklearn.cluster import KMeans, AgglomerativeClustering
import numpy as np
from fastdtw import fastdtw

Layout = dbc.Container([
    dcc.Store(id='[PlotsTwist]data_input', storage_type='session'),
    dcc.Store(id='[PlotsTwist]data_tiny', storage_type='session'),  # 保存tiny信息
    dcc.Store(id='[PlotsTwist/Clustering]data_linkage_method', data="ward"),
    dcc.Store(id='[PlotsTwist/Clustering]data_x_axis', data=[None, None]),
    dcc.Store(id='[PlotsTwist/Clustering]data_y_axis', data=[None, None]),
    dcc.Store(id='[PlotsTwist/Clustering]open_time', data=0),
    LayoutHead_PlotTwist,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.Div(
                    [
                        html.Strong("Clustering method:"),
                        dbc.RadioItems(
                            id="[PlotsTwist/Clustering]clustering_method",
                            options=[
                                {"label": "Euclidean distance", "value": "E-distance"},
                                {"label": "Manhattan distance", "value": "M-distance"},
                                {"label": "Dynamic Time Warping", "value": "dtw"},
                                {"label": "k-means", "value": "k-means"},
                            ], value="E-distance"),

                        html.Br(),

                        html.Div(id="[PlotsTwist/Clustering]linkage_method_div"),

                        # dbc.Checklist(id='[PlotsTwist/Clustering]show_contributions', options=[
                        #     {"label": "Show contributions per condition", "value": 1}
                        # ]),

                        html.Strong("Number of clusters/groups:"),
                        dbc.Input(id="[PlotsTwist/Clustering]number_of_clusters", value="2"),

                        html.Div(id="[PlotsTwist/Clustering]verify_clustering_div"),

                        html.Br(),
                        html.Strong("Plot Layout"),
                        html.Br(),

                        html.Div(id="[PlotsTwist/Clustering]xy_axis_div"),

                        # dbc.Button("Download clustered data(csv)", id="[PlotsTwist/Clustering]download_data"),
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
            html.Div(id="[PlotsTwist/Clustering]graph"),
        ], md=Pannel_Rignt),
    ]),

], fluid=Pannel_fluid, style=Pannel_Style)


# 画图
@app.callback(
    Output("[PlotsTwist/Clustering]graph", "children"),
    Output("[PlotsTwist/Clustering]xy_axis_div", "children"),
    Input("[PlotsTwist]data_input", 'data'),
    State("[PlotsTwist]data_tiny", "data"),
    Input("[PlotsTwist/Clustering]number_of_clusters", 'value'),
    Input("[PlotsTwist/Clustering]clustering_method", 'value'),
    Input("[PlotsTwist/Clustering]data_linkage_method", "data"),
    Input("[PlotsTwist/Clustering]data_x_axis", 'value'),
    Input("[PlotsTwist/Clustering]data_y_axis", 'value'),
)
def set_plotly(data_file_content_store, data_tiny_store, number_of_clusters, clustering_method, linkage_method, data_x_axis, data_y_axis):
    if linkage_method == 'ward' and clustering_method != "E-distance":
        linkage_method = 'complete'
    number_of_clusters = int(number_of_clusters)

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
        
    y_val_list = []
    column_name = data_input.columns.tolist()
    
    x_val_list = list(data_input[column_name[0]])

    for i in set_xdata(data_input)[1:]:
        y_val_list.append(list(data_input[i]))

    curves = np.array(y_val_list)

    if clustering_method == 'k-means':
        # 聚类模型的初始化和拟合
        kmeans = KMeans(n_clusters=number_of_clusters, n_init=10)  # k 是你想要的簇（cluster）的数量
        kmeans.fit(curves)

        # 获取类别预测
        predictions = kmeans.predict(curves)
    elif clustering_method == 'E-distance':
        # 使用欧氏距离进行聚类
        cluster_model = AgglomerativeClustering(n_clusters=number_of_clusters, affinity='euclidean', linkage=linkage_method)
        predictions = cluster_model.fit_predict(curves)
    elif clustering_method == 'M-distance':
        # 使用曼哈顿距离进行聚类
        cluster_model = AgglomerativeClustering(n_clusters=number_of_clusters, affinity='manhattan', linkage=linkage_method)
        predictions = cluster_model.fit_predict(curves)
    elif clustering_method == 'dtw':
        # 使用动态时间规整 (Dynamic Time Warping) 进行聚类
        def dtw_distance(x, y):
            distance, _ = fastdtw(x, y)
            return distance

        # 使用DTW距离进行聚类
        distance_matrix = [[dtw_distance(x, y) for y in curves] for x in curves]
        cluster_model = AgglomerativeClustering(n_clusters=number_of_clusters, affinity='precomputed', linkage=linkage_method)
        predictions = cluster_model.fit_predict(distance_matrix)

    graph = []

    for i in range(number_of_clusters):
        fig = go.Figure()
        y_list = []

        for pos, j in enumerate(predictions):
            if j == i:
                y_list.append(y_val_list[pos])

                fig.add_trace(go.Scatter(
                    x=x_val_list,
                    y=y_val_list[pos],
                    mode="markers",
                    name=column_name[pos+1],
                    marker=dict(
                        opacity=0.5  # 设置透明度
                    )
                ))

        y_avg_list = []
        for pos in range(len(x_val_list)):
            tmp = []
            for j in y_list:
                tmp.append(j[pos])
            y_avg_list.append(sum(tmp) / len(tmp))

        fig.add_trace(go.Scatter(
            x=x_val_list,
            y=y_avg_list,
            name="avg"
        ))

        if data_x_axis and data_x_axis[0] != None and data_x_axis[1] != None:
            fig.update_xaxes(range=data_x_axis)
        if data_y_axis and data_y_axis[0] != None and data_y_axis[1] != None:
            fig.update_yaxes(range=data_y_axis)

        # fig.update_layout(height=100)
        fig.update_layout(
            margin=dict(l=50, r=50, t=30, b=20),  # 设置上下左右边距为50像素
            height=200
        )

        graph.append(
            dcc.Graph(figure=fig)
        )

    if data_x_axis == None or (data_x_axis[0] == None and data_x_axis[1] == None):
        data_x_axis = [min(x_val_list), max(x_val_list)]
    if data_y_axis == None or (data_y_axis[0] == None and data_y_axis[1] == None):
        data_y_axis = [np.min(y_val_list), np.max(y_val_list)]

    xy_div = [
        html.Label("Set lower and upper limit of x-axis"),
        dcc.RangeSlider(
            min(x_val_list), max(x_val_list),
            value=data_x_axis,
            id='[PlotsTwist/Clustering]x_axis',
            tooltip={"placement": "bottom", "always_visible": True}
        ),

        html.Br(),

        html.Label("Set lower and upper limit of y-axis"),
        dcc.RangeSlider(
            np.min(y_val_list), np.max(y_val_list),
            value=data_y_axis,
            id='[PlotsTwist/Clustering]y_axis',
            tooltip={"placement": "bottom", "always_visible": True}
        ),

        html.Br(),
    ]
    return graph, xy_div


@app.callback(
    Output("[PlotsTwist/Clustering]data_x_axis", 'value'),
    Input("[PlotsTwist/Clustering]x_axis", 'value'),
)
def set_x_axis(x_axis):
    return x_axis


@app.callback(
    Output("[PlotsTwist/Clustering]data_y_axis", 'value'),
    Input("[PlotsTwist/Clustering]y_axis", 'value'),
)
def set_y_axis(y_axis):
    return y_axis


@app.callback(
    Output("[PlotsTwist/Clustering]linkage_method_div", "children"),
    Input("[PlotsTwist/Clustering]clustering_method", 'value'),
)
def div_linkage_method(clustering_method):
    if clustering_method == "k-means":
        return []
    elif clustering_method == "E-distance":
        return [
            html.Strong("Linkage method"),
            dbc.RadioItems(
                id="[PlotsTwist/Clustering]linkage_method",
                options=[
                    {"label": "Ward", "value": "ward"},
                    {"label": "Complete", "value": "complete"},
                    {"label": "Average", "value": "average"},
                    {"label": "Single", "value": "single"},
                ],
                value="ward"
            ),
            html.Br(),
        ]
    else:
        return [
            html.Strong("Linkage method"),
            dbc.RadioItems(
                id="[PlotsTwist/Clustering]linkage_method",
                options=[
                    {"label": "Complete", "value": "complete"},
                    {"label": "Average", "value": "average"},
                    {"label": "Single", "value": "single"},
                ],
                value="complete"
            ),
            html.Br(),
        ]


@app.callback(
    Output("[PlotsTwist/Clustering]data_linkage_method", "data"),
    Input("[PlotsTwist/Clustering]linkage_method", 'value'),
)
def set_linkage_method(linkage_method):
    return linkage_method
