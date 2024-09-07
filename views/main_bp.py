from flask import Blueprint, render_template
import datetime

main_bp = Blueprint(
    'main_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@main_bp.route("/mechanics")
def mechanics():
    return render_template("index_mechanics.html")


@main_bp.route("/machine_learning")
def machine_learning():
    return render_template("index_machine_learning.html")


def get_healthcheck():
    from database.schema import Healthcheck
    hcs = Healthcheck.query.all()
    active_pubsub = 0
    if len(hcs) == 1:
        hc = hcs[0]
        now = datetime.datetime.utcnow()
        interval = (now - hc.last_hit).total_seconds()
        if interval < 12 * 60:
            active_pubsub = 1
    return active_pubsub


@main_bp.route("/data_engineering")
def data_engineering():
    active_pubsub = get_healthcheck()
    return render_template("index_data_engineering.html", active_pubsub=active_pubsub)


@main_bp.route("/webapps")
def webapps():
    active_pubsub = get_healthcheck()
    return render_template("index_webapps.html", active_pubsub=active_pubsub)


@main_bp.route("/staging/<page_name>")
def staging(page_name):
    template = f"index_{page_name}.html"
    return render_template(template)


@main_bp.route("/index_gentelella")
def index_gentelella():
    # demonstrates frontend, from https://github.com/afourmy/flask-gentelella
    return render_template("index_dash.html")


@main_bp.route('/download_cv', methods=["GET"])
def download_cv():
    from flask import send_from_directory
    return send_from_directory("/app", "Edmiston.pdf", as_attachment=True)


@main_bp.route('/download_dissertation', methods=["GET"])
def download_dissertation():
    from flask import send_from_directory
    return send_from_directory("/app", "Edmiston_dissertation.pdf", as_attachment=True)


@main_bp.route('/', methods=["GET"])
def index():
    return render_template("index.html")
