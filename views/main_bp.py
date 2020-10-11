import sqlalchemy
import base64
import os
from flask import request
from flask import current_app
from flask import Blueprint
import pandas as pd

main_bp = Blueprint(
    'main_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)
# instructions
# https://cloud.google.com/sql/docs/mysql/connect-run
"""
db_user = os.environ["DB_USER"]
db_pass = os.environ["DB_PASS"]
db_name = os.environ["DB_NAME"]
db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
cloud_sql_connection_name = os.environ["CLOUD_SQL_CONNECTION_NAME"]
estr = sqlalchemy.engine.url.URL(
    drivername="postgres+pg8000",
    username=db_user,  # e.g. "my-database-user"
    password=db_pass,  # e.g. "my-database-password"
    database=db_name,  # e.g. "my-database-name"
    query={
        "unix_sock": "{}/{}/.s.PGSQL.5432".format(
            db_socket_dir,  # e.g. "/cloudsql"
            cloud_sql_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
    }
)
if os.environ['FLASK_DEBUG'] == '0':
    ENG = sqlalchemy.create_engine(
        # Equivalent URL:
        # postgres+pg8000://<db_user>:<db_pass>@/<db_name>
        #                         ?unix_sock=<socket_path>/<cloud_sql_instance_name>/.s.PGSQL.5432
        estr
        # ... Specify additional properties here.
    )
else:
    ENG = sqlalchemy.create_engine(os.environ["DB_CONN"])

"""

@main_bp.route('/task', methods=["GET"])
def task():
    current_app.logger.info("hi")
    # df = pd.read_sql("select * from test_df", con=ENG)
    return "hi" 

# [START run_pubsub_handler]
@main_bp.route('/ab', methods=['POST'])
def index():
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
