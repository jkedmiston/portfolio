# Summary
Portfolio of integrated app capabilities (WIP), and notes to myself on how to build it. 
* [URL to app](https://jke-portfolio.herokuapp.com)

## Features
This Python/Flask application itself features the following:
- Integration with Plotly Dash for dashboards
- Front end design via Flask-Gentelella
- Back end has Postgres database
- Back end has Celery available via Redis with Beat and Worker containers
- SQLAlchemy, Flask-Migrate for version tracking database updates
- Flask Admin, for quick DBAdmin as well as useful features for startup stage companies. 

# First usage
## GCP
For local development, the GCP configuration for service account credentials and Pub/Sub must be set up on your own (in order to perform operations on Google slides). These instructions are:  
* Create a GCP project.
* Create a service account for the project, and download the `json` key. 
* Create a GCP Pub/Sub topic `portfolio-demo` and subscription `portfolio-subscription` subscribed to that topic with pull mode. 
Copy `.env.sample` to `.env`. Populate with credentials from the `json` key if exercising the Google integrations (primarily `GOOGLE_APPLICATION_CREDENTIALS`. 

## Intel realsense
For local development with a realsense camera, the command `xhost +local:root` must be used to enable `realsense-viewer` to work in the Docker container.
* Speaking from experience on Ubuntu 20.04, do not install Docker with `snap install docker`, instead use `apt-get install docker`.

# Build and test:
On Mac OS
* `docker-compose build`
* `docker-compose run --rm web python -m pytest`
* `docker-compose -f docker-compose-intel.yml build`
* `docker-compose -f docker-compose-intel.yml up`

On a clean ubuntu install, I had to do the following to avoid using `sudo` in subsequence `docker-compose` commands, e.g. `docker-compose build`, this is based on [instructions here](https://docs.docker.com/engine/install/linux-postinstall/)
* `sudo groupadd docker`
* `sudo usermod -aG docker $USER`
* Log out and back in.

Then, one can run the same commands as above in the MacOS section without `sudo`.

## Testing
To execute test pipeline
* `docker-compose run --rm web python -m pytest `

To execute a single test
* `docker-compose run --rm web python -m pytest -k (name of test)` e.g. 
* `docker-compose run --rm web python -m pytest -k test_basic_grouping_plots`

# Features

## Testing plots
For adjusting the `matplotlib` plots produced in the Google slides demo part of the app, by trial-and-error, I run the plotting functions via an Anaconda environment outside the Docker container. To run tests in this way, once `PYTHONPATH` is set up, and `requirements.txt` is installed with `pip install -r requirements.txt`, then use e.g. `python -m pytest -k test_basic_bar_plots`. The logic in `conftest.py` sets up `sys._called_from_test` as suggested in the `pytest` docs [here](https://docs.pytest.org/_/downloads/en/3.0.1/pdf/). 

## Flask migrate
Setting up flask migrate took a bit. This was helpful. 
* https://blog.miguelgrinberg.com/post/how-to-add-flask-migrate-to-an-existing-project

## Flask forms
- https://hackersandslackers.com/flask-wtforms-forms/
- https://flask.palletsprojects.com/en/1.1.x/patterns/wtforms/#the-forms

## Plotly Dash integration
* CSRF issue resolved by this solution https://stackoverflow.com/a/51618986

# Development procedure
## Python side
Starting up the app so that breakpoints are easy to work in can be done with: 
* `docker-compose run --rm -p 5000:5000 web python3 -m pdb wsgi.py`
* Then open up `localhost:5000` in a browser and you can interact with the front end/back end functionality.

## Docker iterations
For iterating on the `Dockerfile` (e.g. what packages are needed in the container, etc), start up the app with the command `/bin/bash`, e.g. `docker-compose run --rm web /bin/bash` then when in that container run the `apt-get install` packages needed to compile codes, etc. e.g. for the `realsense` tests, `g++ rs-imshow.cpp  -I/usr/include/opencv4 -lrealsense2 -lopencv_core -lopencv_imgproc -lopencv_highgui` was found with some iteration of this nature. The order of `opencv` libraries to add in order of common use is given [here](https://stackoverflow.com/questions/9094941/compiling-opencv-in-c)
```
  -lopencv_core
  -lopencv_imgproc
  -lopencv_highgui
  -lopencv_imagecodecs
  -lopencv_ml
  -lopencv_video
  -lopencv_features2d
  -lopencv_calib3d
  -lopencv_objdetect
  -lopencv_contrib
  -lopencv_legacy
  -lopencv_flann
```

# Installing `librealsense`
Setting up the Intel realsense camera took a bit, for a good starting point the github page for `librealsense` is [here](https://github.com/IntelRealSense/librealsense/blob/master/doc/installation.md)
* To run:
* Inspired by instructions [here](https://github.com/edowson/docker-intel).

If the client computer (connected to the camera) is an Ubuntu 20.04 machine, the following worked to start up the `realsense-viewer` gui and confirm that the application is working. 
```
jedmiston@je-hp: $ docker-compose -f docker-compose-intel.yml build
jedmiston@je-hp: $ xhost +local:root
non-network local connections being added to access control list
jedmiston@je-hp: $ docker-compose -f docker-compose-intel.yml up
[opens up intel GUI]
jedmiston@je-hp: $ xhost -local:root
```
In terms of raw docker cli commands instead of `docker-compose`: 
```
jedmiston@je-hp: $ xhost +local:root
non-network local connections being added to access control list
jedmiston@je-hp: $ docker run -it -e DISPLAY=$DISPLAY -e QT_GRAPHICSSYSTEM=native -e QT_X11_NO_MITSHM=1 -v /dev:/dev -v /lib/modules:/lib/modules -v /tmp/.X11-unix:/tmp/.X11-unix --privileged --cap-add=ALL --rm etl:latest /bin/bash
root@6956ef978d70:/app# realsense-viewer
[opens up intel GUI]
jedmiston@je-hp: $ xhost -local:root
non-network local connections being removed from access control list
```

# Emacs setup
* `emacs.el` in this repository contains a config file for environments.
* From a quick standpoint, in early 2021 this is what worked for me to set up on Ubuntu 20.04: 
* `sudo apt-get install emacs python3 python-is-python3`
* Move start file to emacs home. 
* `cp emacs.el ~/.`
* Download Anaconda, set up `conda create -n portfolio python==3.8`
* Then load the environment and do `(portfolio)$ pip install jedi flake8 yapf autopep8 black rope`
* In emacs session, install MELPA packages using `M-x list-packages` and then searching for and selecting
* `elpy`
* `virtualenvwrapper`
* `py-autopep8`
* You can use in emacs, `M-x elpy-config` to list out the configuration for the loaded environments and make sure the virtual environment is detected. 

# GCP Pub/Sub
For command line input for a new Pub/Sub combination: 
```
$ gcloud pubsub topics create mpi-pubsub-topic
$ gcloud pubsub subscriptions create mpi-pubsub-topic-subscription --topic=portfolio-topic --ack-deadline=10 --expiration-period=never
```

## GCP Cloud Functions
The directory to be uploaded should contain a function with the given name (e.g. `run(event, context)`). 
These require a `.env.yaml` file with the format
$ cat .env.yaml
```
SECRET: my_secret
GOOGLE_APPLICATION_CREDENTIALS: ...
RETURN_TOPIC: pubsub-return-topic
```

```
* Create topic and cloud function on the topic
$ gcloud pubsub topics create mpi-cloud-function-topic
$ gcloud pubsub topics create mpi-cloud-function-topic-return
```

The `mpi-cloud-function-topic-return` should be set as `RETURN_TOPIC` in `.env.yaml`
```
$ gcloud functions deploy mpi-cloud-function --runtime python38 --trigger-topic=mpi-cloud-function-topic --memory=1GB --source=/home/jedmiston/projects/portfolio/google_functions/deployment/mpi_cloud_function --entry-point=run --timeout=540 --env-vars-file=/home/jedmiston/projects/portfolio/google_functions/deployment/mpi_cloud_function/.env.yaml
```

If this is all working, then running
```
docker-compose run --rm web python -i scripts/upload_to_cloud_function_and_aggregate.py
```
will produce the output
```
Message 0 2267090376785753 published
Message 1 2267083187798302 published
Message 2 2267078805545247 published
Message 3 2267091059140614 published
Cloud function results......
cloud function's process_data([1, 10, 100]) -> 74.0
local process_data([1, 10, 100]) -> 74.0
cloud function's process_data([4, 5, 6]) -> 10.0
local process_data([4, 5, 6]) -> 10.0
cloud function's process_data([10, 11, 12]) -> 22.0
local process_data([10, 11, 12]) -> 22.0
cloud function's process_data([3, 5, 10]) -> 12.0
local process_data([3, 5, 10]) -> 12.0
```
