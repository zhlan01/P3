import flask
from flask import send_file, send_from_directory, make_response
from dash import html, dcc, dash_table

import os
import uuid

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
PATH = '/www/wwwroot/server/DataProcessing'

def is_safe_path_component(value):
    """Reject path traversal and absolute paths in user-controlled names."""
    if not value or value in (".", ".."):
        return False
    if len(value) > 200 or value.startswith(".") or ".." in value:
        return False
    if any(ch in value for ch in ("/", "\\", "\x00")):
        return False
    if any(ord(ch) < 32 for ch in value):
        return False
    return True


@server.route('/upload/<fileuuid>/<filename>', methods=['GET'])
def download_file(fileuuid, filename):
    if not is_safe_path_component(fileuuid) or not is_safe_path_component(filename):
        flask.abort(404)

    upload_root = os.path.realpath(os.path.join(PATH, "upload"))
    directory = os.path.realpath(os.path.join(upload_root, fileuuid))
    if not directory.startswith(upload_root + os.sep):
        flask.abort(404)

    response = make_response(send_from_directory(directory, filename, as_attachment=True))
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename.encode().decode('latin-1'))
    return response

app = dash.Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=["/assets/js/bootstrap-5.3.1/bootstrap.min.css"],
    use_pages=False,
    routes_pathname_prefix='/',
    pages_folder="pages",
    prevent_initial_callbacks='initial_duplicate',
    title="Computing Medical",
    serve_locally=False
)

server = app.server

UPLOAD_API = "/API/resumable"
ALLOWED_UPLOAD_EXTENSIONS = {".csv", ".xls", ".xlsx", ".json"}


@server.before_request
def guard_resumable_upload():
    """Block path traversal and unsafe uploads on the dash-uploader API."""
    if flask.request.path != UPLOAD_API:
        return
    if flask.request.method not in ("GET", "POST"):
        return

    source = flask.request.form if flask.request.method == "POST" else flask.request.args
    upload_id = source.get("upload_id", "")
    identifier = source.get("resumableIdentifier", "")
    filename = source.get("resumableFilename", "")

    if upload_id:
        try:
            uuid.UUID(upload_id)
        except (ValueError, TypeError, AttributeError):
            flask.abort(400, "Invalid upload_id")

    if not is_safe_path_component(identifier):
        flask.abort(400, "Invalid resumableIdentifier")
    if not is_safe_path_component(filename):
        flask.abort(400, "Invalid resumableFilename")

    if flask.request.method == "POST":
        extension = os.path.splitext(filename)[1].lower()
        if extension not in ALLOWED_UPLOAD_EXTENSIONS:
            flask.abort(400, "File type not allowed")

        total = flask.request.form.get("resumableTotalChunks", type=int)
        if total is not None and (total < 1 or total > 10000):
            flask.abort(400, "Invalid chunk count")

        chunk = flask.request.form.get("resumableChunkNumber", type=int)
        if chunk is not None and chunk < 1:
            flask.abort(400, "Invalid chunk number")

        if flask.request.content_length and flask.request.content_length > 16 * 1024 * 1024:
            flask.abort(413, "Chunk too large")
