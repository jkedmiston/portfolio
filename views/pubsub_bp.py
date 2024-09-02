"""
Primary demo here is GCP Pub/Sub to send commands to an Intel Realsense depth camera in my home office.
"""
from extensions import db
from database.schema import PubSubMessage, CloudFunction
import numpy as np
import requests
import plotly.graph_objs as go
import plotly.offline as pyo
import plotly.io as pio
from misc_utilities import generate_uuid
from google_functions.pubsub import publish_message
from google_functions.google_storage import get_signed_url_from_fname
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms import TextAreaField
from flask_wtf import FlaskForm
from flask import (request,
                   flash,
                   current_app,
                   url_for,
                   redirect,
                   Blueprint,
                   render_template)
import datetime
import os
import json
import time


pubsub_bp = Blueprint(
    'pubsub_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


def download_file_from_signed_url(signed_url, local_filename):
    try:
        # Send a GET request to the signed URL
        response = requests.get(signed_url)

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Open a local file in write-binary mode
        with open(local_filename, 'wb') as file:
            file.write(response.content)

        print(f"File downloaded successfully and saved as {local_filename}")
        return local_filename
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")


@pubsub_bp.route("/pubsub_depth_cam", methods=["GET", "POST"])
def pubsub_depth_cam():
    """
    triggers a depth camera photo, and presents the result to screen
    """

    from celery_jobs import catch_pubsub_message

    class SheetForm(FlaskForm):
        submit = SubmitField("Trigger photo", render_kw={"id": "btn",
                             "class": "btn btn-primary"})

    form = SheetForm(request.form)
    t0 = time.time()
    if form.validate_on_submit():
        unique_tag = generate_uuid()
        publish_message(
            topic_name=os.environ["SERVER_TO_DEPTH_CAM_TOPIC"], data={'unique_tag': unique_tag})
        url = None
        url_data = None
        image_fname = None
        success = False
        while time.time() - t0 < 25:
            catch_pubsub_message(
                subscription_id=os.environ["DEPTH_CAM_TO_SERVER_SUBSCRIPTION"])

            psm = PubSubMessage.query.filter(
                PubSubMessage.unique_tag == unique_tag).first()
            if psm is None:
                current_app.logger.info(
                    "continuing to wait for depth cam image")
                continue

            if "colormap" in psm.data:
                colormap = psm.data["colormap"]  # colormap file
                time_of_photo = psm.publish_time
                success = True
                # show this in the url

                url = get_signed_url_from_fname(colormap)
                if "fname" in psm.data:
                    url_data = get_signed_url_from_fname(psm.data["fname"])
                    image_fname = download_file_from_signed_url(
                        url_data, f"loc_{unique_tag}.txt")
                    from database.schema import Healthcheck
                    hcs = Healthcheck.query.all()
                    if len(hcs) == 0:
                        hc = Healthcheck(last_hit=datetime.datetime.utcnow())
                        db.session.add(hc)
                        db.session.commit()
                    else:
                        hc = hcs[0]
                        hc.last_hit = datetime.datetime.utcnow()
                        db.session.commit()
                break
            else:
                flash("Hardware error")
                current_app.logger.error("Hardware error")
                return redirect(url_for("pubsub_bp.pubsub_depth_cam"))

        if success is False:
            flash("Hardware error")
            return redirect(url_for("pubsub_bp.pubsub_depth_cam"))

        fig_html = None
        if url:
            #
            if image_fname:
                current_app.logger.info("reading %s" % image_fname)
                arr = np.loadtxt(image_fname)
                shape = arr.shape
                xs = np.arange(shape[1])
                ys = np.arange(shape[0])
                X, Y = np.meshgrid(xs, ys)
                # Create a 3D surface plot
                surface = go.Surface(
                    x=X,
                    y=Y,
                    z=arr
                )
                # Layout for the plots
                layout = go.Layout(
                    title='3D Surface Plot - Depth Cam',
                    scene=dict(
                        xaxis_title='X Axis',
                        yaxis_title='Y Axis',
                        zaxis_title='Z Axis'
                    )
                )
                fig = go.Figure(data=[surface], layout=layout)
                fig_html = pio.to_html(
                    fig, include_plotlyjs=True, full_html=False)

            return render_template('pubsub/pubsub_results.html',
                                   link="Link to photo",
                                   link_data="Link to 3D data",
                                   time_of_photo=time_of_photo,
                                   fig_html=fig_html,
                                   url=url,
                                   url_data=url_data)
        else:
            return redirect(url_for('pubsub_bp.pubsub_depth_cam'))

    form_html = render_template('partials/reports/basic_form.html',
                                form=form,
                                action=url_for('pubsub_bp.pubsub_depth_cam'))

    return render_template('pubsub/pubsub_demo.html',
                           form_html=form_html)


@pubsub_bp.route("/pubsub_demo", methods=["GET", "POST"])
def pubsub_demo():
    # publish a pubsub, and receive
    from celery_jobs import catch_pubsub_message

    class SheetForm(FlaskForm):
        message = StringField('PubSub message', validators=[DataRequired()])
        submit = SubmitField("Submit", render_kw={"id": "btn",
                                                  "class": "btn btn-primary spinner"})

    form = SheetForm(request.form)
    if form.validate_on_submit():
        # send pub sub
        current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        unique_tag = generate_uuid()
        publish_message(topic_name="portfolio-demo", data={"dummy": 1,
                                                           "unique_tag": unique_tag,
                                                           "current_time": current_time, "message": form.data["message"]})
        catch_pubsub_message.delay(subscription_id="portfolio-subscription")
        return redirect(url_for("pubsub_bp.success", unique_tag=unique_tag))

    form_html = render_template('partials/reports/basic_form.html',
                                form=form,
                                action=url_for('pubsub_bp.pubsub_demo'))

    return render_template('pubsub/pubsub_basic.html',
                           form_html=form_html)


@pubsub_bp.route("/pubsub_demo_success", methods=["GET"])
def success():
    import time
    unique_tag = request.args.get("unique_tag")
    for j in range(20):
        message = PubSubMessage.query.filter(
            PubSubMessage.unique_tag == unique_tag).first()
        if message is None:
            time.sleep(1)
            print(j)
    if message:
        return "Success: You Entered {}".format(json.dumps(message.data["message"]))
    return "Unable to catch message before Heroku timeout"


@pubsub_bp.route("/demo_cloud_function", methods=["GET"])
@pubsub_bp.route("/demo_cloud_function/<cloud_def>", methods=["GET"])
@pubsub_bp.route("/demo_cloud_function/<cloud_def>/<data_def>", methods=["GET"])
def demo_cloud_function(cloud_def=None, data_def=None):
    if cloud_def is not None:
        cl = CloudFunction.query.get(cloud_def)
        cloud_def = cl.definition

    return render_template("cloud_definition.html", cloud_def=cloud_def, data_def=data_def)


@pubsub_bp.route("/custom_cloud_function", methods=["GET", "POST"])
def custom_cloud_function():
    # Take in a simple function definition from the user.
    # Take in 3 sets of data to process.
    # Output the results of the function on each set of data.
    class SheetForm(FlaskForm):
        func_def = TextAreaField('Function definition',
                                 validators=[DataRequired()], render_kw={"rows": 15, "cols": 48})
        submit = SubmitField("Submit")

    form = SheetForm(request.form)
    if form.validate_on_submit():
        func_def = form.data["func_def"]
        cl = CloudFunction(definition=func_def)
        db.session.add(cl)
        db.session.commit()
        return redirect(url_for('pubsub_bp.demo_cloud_function', cloud_def=cl.id))

    return render_template("custom_cloud_function.html", form=form)
