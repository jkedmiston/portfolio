"""
Primary demo here is GCP Pub/Sub to send commands to an Intel Realsense depth camera in my home office.
"""
import os
import json
import datetime
from flask import (request,
                   current_app,
                   url_for,
                   redirect,
                   Blueprint,
                   render_template)

from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField

from google_functions.google_storage import get_signed_url_from_fname
from google_functions.pubsub import publish_message
from misc_utilities import generate_uuid
from database.schema import PubSubMessage, CloudFunction
from extensions import db

pubsub_bp = Blueprint(
    'pubsub_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@pubsub_bp.route("/pubsub_depth_cam", methods=["GET", "POST"])
def pubsub_depth_cam():
    """
    triggers a depth camera photo, and presents the result to screen
    """

    from celery_jobs import catch_pubsub_message

    class SheetForm(FlaskForm):
        submit = SubmitField("Trigger photo")

    form = SheetForm(request.form)
    if form.validate_on_submit():
        unique_tag = generate_uuid()
        publish_message(
            topic_name=os.environ["SERVER_TO_DEPTH_CAM_TOPIC"], data={'unique_tag': unique_tag})

        while True:
            catch_pubsub_message(
                subscription_id=os.environ["DEPTH_CAM_TO_SERVER_SUBSCRIPTION"])

            psm = PubSubMessage.query.filter(
                PubSubMessage.unique_tag == unique_tag).first()
            if psm is None:
                current_app.logger.info(
                    "continuing to wait for depth cam image")
                continue

            colormap = psm.data["colormap"]  # colormap file
            time_of_photo = psm.publish_time

            # show this in the url

            url = get_signed_url_from_fname(colormap)
            break

        return render_template('pubsub/pubsub_results.html',
                               link="Link to photo",
                               time_of_photo=time_of_photo,
                               url=url)

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
        submit = SubmitField("Submit")

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
