import sqlalchemy
import base64
import os
from flask import request
from flask import current_app, url_for, redirect
from flask_login import current_user
from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from google_functions.pubsub import publish_message

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
        # send pub subfig
        publish_message(topic_name="portfolio-demo", data={"dummy": 1})
        #
        catch_pubsub_message.delay(subscription_id="portfolio-subscription")
        return redirect(url_for("pubsub_bp.success"))

    form_html = render_template('partials/reports/basic_form.html',
                                form=form,
                                action=url_for('pubsub_bp.pubsub_demo'))

    return render_template('pubsub/pubsub_demo.html',
                           form_html=form_html)
