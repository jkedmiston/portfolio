import sqlalchemy
import base64
import os
from flask import request
from flask import current_app, url_for, redirect
from flask_login import current_user
from flask import Blueprint, render_template
import pandas as pd

main_bp = Blueprint(
    'main_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)
# instructions
# https://cloud.google.com/sql/docs/mysql/connect-run


@main_bp.route("/index_gentelella")
def index_gentelella():
    # demonstrates frontend, from https://github.com/afourmy/flask-gentelella
    return render_template("index_dash.html")

@main_bp.route('/task', methods=["GET"])
def task():
    current_app.logger.info("hi")
    # df = pd.read_sql("select * from test_df", con=ENG)
    return render_template("d3.html")

@main_bp.route('/task2', methods=["GET"])
def task2():
    current_app.logger.info("hi")
    # df = pd.read_sql("select * from test_df", con=ENG)
    return render_template("d3_2.html")

@main_bp.route('/download_cv', methods=["GET"])
def download_cv():
    from flask import send_from_directory
    return send_from_directory("/app", "Edmiston_2020.pdf", as_attachment=True)


@main_bp.route('/test_schema', methods=["GET"])
def test_schema():
    # init_all
    from database.schema import ExampleData
    from extensions import db
    
    e = ExampleData(alias="hello")
    db.session.add(e)
    db.session.commit()
    print("number of pts", len(ExampleData.query.all()))
    return redirect(url_for("main_bp.index"))

@main_bp.route('/', methods=["GET"])
def index():
    return render_template("index.html")

# [START run_pubsub_handler]
@main_bp.route('/ab', methods=['POST'])
def ab():
    # pubsub push for ETL subscription
    envelope = request.get_json()
    if not envelope:
        msg = 'no Pub/Sub message received'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    pubsub_message = envelope['message']

    name = 'World'
    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        name = base64.b64decode(pubsub_message['data']).decode('utf-8').strip()

    print(f'Hello {name}!')

    return ('', 204)
# [END run_pubsub_handler]
