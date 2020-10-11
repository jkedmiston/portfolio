# Copyright 2019 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import dash
from flask import Flask, request, g
import time
import datetime
from flask import current_app
import logging


def register_request_logger(app):
    def _before_request():
        g.request_start_time = time.time()

    def _after_request(response):
        """ Logging useful information after every request. """

        # if current_user.is_authenticated:
        #    requester_email = current_user.email
        # else:
        #    requester_email = 'unauthenticated user'

        request_end_time = time.time()
        seconds = request_end_time - g.request_start_time
        request_duration = datetime.timedelta(seconds=seconds).total_seconds()
        requester_email = "email"
        current_app.logger.info(
            "%s [%s] %s %s %s %s %s %s %s %s %s %s %ss",
            request.remote_addr,
            datetime.datetime.utcnow().strftime("%d/%b/%Y:%H:%M:%S.%f")[:-3],
            request.method,
            request.path,
            request.scheme,
            response.status,
            response.content_length,
            request.referrer,
            request.user_agent,
            request.data,
            request.form,
            requester_email,
            request_duration
        )

        return response

    app.before_request(_before_request)
    app.after_request(_after_request)


def register_stylized_dashapp(app):
    from dashboards.dash_files.dash_pk_calc.app import (
        define_layout,
        define_callbacks,
    )
    # https://community.plot.ly/t/how-do-i-use-dash-to-add-local-css/4914/4
    # https://github.com/plotly/dash/issues/71

    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport",
                     "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}  # noqa
    dashapp1 = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/pk/',
                         assets_folder="dashboards/dash_files/dash_pk_calc/assets",
                         meta_tags=[meta_viewport])

    if (dashapp1.logger.hasHandlers()):
        dashapp1.logger.handlers.clear()

    with app.app_context():
        dashapp1.title = "Test"
        define_layout(dashapp1)
        define_callbacks(dashapp1)
        
    # protect_dashviews(dashapp1)
    
def create_app():
    from views.main_bp import main_bp
    from config import Config

    app = Flask(__name__, instance_relative_config=False, static_folder="static")
    app.config.from_object(Config)
    app.logger.setLevel(logging.INFO)
    with app.app_context():
        register_request_logger(app)
        app.register_blueprint(main_bp)
        register_stylized_dashapp(app)
        return app
