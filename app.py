import flask
from flask import send_file, send_from_directory, make_response
from dash import html, dcc, dash_table

import dash
import dash_bootstrap_components as dbc

LayoutHead_PlotsOfData = html.Div([
    html.H2("PSPV - Python-based Statistical Parameters Visualization"),
    html.Hr(),
], style={"margin-top": "20px", "margin-bottom": "20px"})

LayoutHead_PlotTwist = html.Div([
    html.H2("PTDV - Python-based Time-series Data Visualization"),
    html.Hr(),
], style={"margin-top": "20px", "margin-bottom": "20px"})

LayoutHead_VolcaNoseR = html.Div([
    html.H2("PVV - Python-based Visualization with Volcano"),
    html.Hr(),
], style={"margin-top": "20px", "margin-bottom": "20px"})

Pannel_Left = 3
Pannel_Rignt = 9
Pannel_Style = {"width": "95%"}
Pannel_fluid = True

server = flask.Flask(__name__)
PATH = '/www/wwwroot/DataProcessing'

@server.route('/upload/<fileuuid>/<filename>', methods=['GET'])
def download_file(fileuuid, filename):
    if './' in fileuuid or './' in filename:
        return
    
    directory = f"{PATH}/upload/{fileuuid}"
    response = make_response(send_from_directory(directory, filename, as_attachment=True))
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename.encode().decode('latin-1'))
    return response

app = dash.Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=False,
    routes_pathname_prefix='/',
    pages_folder="pages",
    prevent_initial_callbacks='initial_duplicate',
    title="Computing Medical",
    serve_locally=False
)

server = app.server
