# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.7-buster

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY requirements.txt .
COPY gcp_service_account.json .

RUN apt-get update && apt-get install texlive-latex-extra -y && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" |  tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && apt-get install apt-transport-https ca-certificates gnupg && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg |  apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && apt-get update && apt-get -y install google-cloud-sdk && gcloud auth activate-service-account --key-file gcp_service_account.json

RUN python3 -m pip install -r requirements.txt

# In order to have similar builds for local dev on MacOS and Ubuntu,
# and deployment on Heroku, this custom library here needs a separate
# line item currently. 
RUN cd /root/ && git clone https://github.com/jkedmiston/latex-ds.git && cd latex-ds && python setup.py build && python setup.py install 

ENV PYTHONPATH "${PYTHONPATH}:/app"
COPY . /app/.
RUN mkdir /app/tmp

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "main:create_app()"

