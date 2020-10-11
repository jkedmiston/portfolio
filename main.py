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


def create_app():
    from views.main_bp import main_bp
    from config import Config

    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)
    app.logger.setLevel(logging.INFO)
    with app.app_context():
        register_request_logger(app)
        app.register_blueprint(main_bp)
        return app
