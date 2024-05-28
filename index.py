import dash
from dash import dcc
from dash import html
from app import app

# 引入页面文件
import os
import glob
import importlib

"""
https://github.com/JoachimGoedhart/PlotTwist

https://github.com/JoachimGoedhart/PlotsOfData

https://github.com/JoachimGoedhart/VolcaNoseR

https://huygens.science.uva.nl/
"""

def import_all_py_files(folder_path):
    py_files = glob.glob(os.path.join(folder_path, "*.py"))
    for py_file in py_files:
        module_name = os.path.splitext(os.path.basename(py_file))[0]
        module = importlib.import_module(f"{folder_path.replace('/', '.')}.{module_name}")
        globals()[module_name] = module


import_all_py_files('pages/PlotsOfData')
import_all_py_files('pages/PlotTwist')
import_all_py_files('pages/VolcaNoseR')
import_all_py_files('pages/DataFormatConvert')

from pages import PlotsOfData, PlotTwist, VolcaNoseR, DataFormatConvert

# 主页导航选择

url_bar_and_content_div = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Iframe(srcDoc=open('assets/nav.html').read(), style={"width": "100vw", "height": "56px", "vertical-align": "bottom"}, id='iframe'),
    html.Div(id='page-content')
])

index_page = html.Div([
    html.Iframe(srcDoc=open('assets/index.html').read(), style={"width": "100vw", "height": "calc(100vh - 56px)", "vertical-align": "bottom"}, id='iframe'),
])

app.layout = url_bar_and_content_div
app.validation_layout = html.Div([
    url_bar_and_content_div,
    index_page,
    PlotsOfData.PlotsOfData.Layout,
    PlotsOfData.Plot.Layout,
    PlotsOfData.Clustering.Layout,
    PlotsOfData.DataSummary.Layout,
    PlotsOfData.About.Layout,
    PlotTwist.PlotTwist.Layout,
    PlotTwist.Plot.Layout,
    PlotTwist.Clustering.Layout,
    PlotTwist.DataSummary.Layout,
    PlotTwist.About.Layout,
    VolcaNoseR.VolcaNoseR.Layout,
    VolcaNoseR.Plot.Layout,
    VolcaNoseR.About.Layout,
    DataFormatConvert.DataFormatConvert.Layout(),
])

@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/PlotsOfData':
        return PlotsOfData.PlotsOfData.Layout
    elif pathname == '/PlotTwist':
        return PlotTwist.PlotTwist.Layout
    elif pathname == '/VolcaNoseR':
        return VolcaNoseR.VolcaNoseR.Layout
    elif pathname == '/DataFormatConvert':
        return DataFormatConvert.DataFormatConvert.Layout()


    elif pathname == '/PlotsOfData/Plot':
        return PlotsOfData.Plot.Layout
    elif pathname == '/PlotTwist/Plot':
        return PlotTwist.Plot.Layout
    elif pathname == '/VolcaNoseR/Plot':
        return VolcaNoseR.Plot.Layout

    elif pathname == '/PlotsOfData/DataSummary':
        return PlotsOfData.DataSummary.Layout
    elif pathname == '/PlotTwist/DataSummary':
        return PlotTwist.DataSummary.Layout

    elif pathname == '/PlotsOfData/Clustering':
        return PlotsOfData.Clustering.Layout
    elif pathname == '/PlotTwist/Clustering':
        return PlotTwist.Clustering.Layout

    elif pathname == '/PlotsOfData/About':
        return PlotsOfData.About.Layout
    elif pathname == '/PlotTwist/About':
        return PlotTwist.About.Layout
    elif pathname == '/VolcaNoseR/About':
        return VolcaNoseR.About.Layout
    else:
        return index_page


if __name__ == '__main__':
    app.run_server(debug=False)
