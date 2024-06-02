import os
from flask import request, flash
from flask import current_app, url_for, redirect
from flask_login import current_user
import datetime
from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from google_functions.pubsub import publish_message
from misc_utilities import generate_uuid
from database.schema import PubSubMessage

pubsub_bp = Blueprint(
    'pubsub_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@pubsub_bp.route("/pubsub_demo_success", methods=["GET"])
def success():
    return "Success"


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
        publish_message(topic_name="portfolio-demo", data={"dummy": 1,
                                                           "unique_tag": generate_uuid(),
                                                           "current_time": current_time})
        #
        catch_pubsub_message.delay(subscription_id="portfolio-subscription")
        return redirect(url_for("pubsub_bp.success"))

    form_html = render_template('partials/reports/basic_form.html',
                                form=form,
                                action=url_for('pubsub_bp.pubsub_demo'))

    return render_template('pubsub/pubsub_demo.html',
                           form_html=form_html)


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

            if "colormap" in psm.data:
                colormap = psm.data["colormap"]  # colormap file
                time_of_photo = psm.publish_time
                # show this in the url
                from google_functions.google_storage import get_signed_url_from_fname
                url = get_signed_url_from_fname(colormap)
            else:
                flash("Hardware error")
                return redirect(url_for('pubsub_bp.pubsub_depth_cam'))
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
