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

# Build and test:
On Mac OS
* `docker-compose build`
* `docker-compose run --rm web python -m pytest`
* `docker-compose -f docker-compose-intel.yml build`
* `docker-compose -f docker-compose-intel.yml up`

On a clean ubuntu install, I had to do the following to avoid using `sudo`, based on
[instructions here](https://docs.docker.com/engine/install/linux-postinstall/)
* `sudo groupadd docker`
* `sudo usermod -aG docker $USER`
* Log out and back in.

Then, one can run the same commands as above in the MacOS section without `sudo`.

# Features

## Testing plots
For adjusting the `matplotlib` plots by trial-and-error, I run the plotting funcations via an Anaconda environment outside the Docker container. To run tests in this way, once `PYTHONPATH` is set up, and `requirements.txt` is installed with `pip install -r requirements.txt`, then use e.g. `python -m pytest -k test_basic_bar_plots`. The logic in `conftest.py` sets up `sys._called_from_test` as suggested in the `pytest` docs [here](https://docs.pytest.org/_/downloads/en/3.0.1/pdf/). 

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
## Docker iterations
Start up the app with `/bin/bash`, then run the `apt-get install` packages needed to compile codes, etc. e.g. for the `realsense` tests, `g++ rs-imshow.cpp  -I/usr/include/opencv4 -lrealsense2 -lopencv_core -lopencv_imgproc -lopencv_highgui` was found with some iteration.


# Installing `librealsense`
See [here](https://github.com/IntelRealSense/librealsense/blob/master/doc/installation.md)
* To run:
* Inspired by instructions [here](https://github.com/edowson/docker-intel)
On a straight Ubuntu 20.04 machine, the following worked. 
```
jedmiston@je-hp: $ xhost local:root
non-network local connections being added to access control list
jedmiston@je-hp: $ docker-compose up intel-cam
[opens up intel GUI]
```
In terms of docker cli commands:
```
jedmiston@je-hp: $ xhost local:root
non-network local connections being added to access control list
jedmiston@je-hp: $ docker run -it -e DISPLAY=$DISPLAY -e QT_GRAPHICSSYSTEM=native -e QT_X11_NO_MITSHM=1 -v /dev:/dev -v /lib/modules:/lib/modules -v /tmp/.X11-unix:/tmp/.X11-unix --privileged --cap-add=ALL --rm etl:latest /bin/bash
root@6956ef978d70:/app# realsense-viewer
[opens up intel GUI]
jedmiston@je-hp: $ xhost -local:root
non-network local connections being removed from access control list
```
