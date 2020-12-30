import os
import json


def get_service_account_email():
    env_vars = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    email = env_vars["client_email"]
    return email
