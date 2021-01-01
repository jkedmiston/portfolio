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
For local development, the GCP configuration for credentials and Pub/Sub must be set up on your own. 
* Create a GCP project.
* Create a service account for the project, and download the `json` key. 
* Create a GCP Pub/Sub topic `portfolio-demo` and subscription `portfolio-subscription` subscribed to that topic with pull mode. 
Copy `.env.sample` to `.env`. Populate with credentials from the `json` key if exercising the Google integrations (primarily `GOOGLE_APPLICATION_CREDENTIALS`. 

Build and test:
On Mac OS
* `docker-compose build`
* `docker-compose run --rm web python -m pytest`

On a clean ubuntu install, I had to do the following, based on
[instructions here](https://docs.docker.com/engine/install/linux-postinstall/)
* `sudo groupadd docker`
* `sudo usermod -aG docker $USER`
* Log out and back in.

Then, one can run the following without `sudo`.
* `docker-compose build`
* `docker-compose run --rm web python -m pytest`

# Heroku setup
* `heroku stack:set container --app jke-portfolio`

# Development procedure
Starting up the app so that breakpoints are easy to work in: 
* `docker-compose run --rm -p 5000:5000 web python3 -m pdb wsgi.py`

## Testing plots
For adjusting the `matplotlib` plots by trial-and-error, I run the plotting funcations via an Anaconda environment outside the Docker container. To run tests in this way, once `PYTHONPATH` is set up, and `requirements.txt` is installed with `pip install -r requirements.txt`, then use e.g. `python -m pytest -k test_basic_bar_plots`. The logic in `conftest.py` sets up `sys._called_from_test` as suggested in the `pytest` docs [here](https://docs.pytest.org/_/downloads/en/3.0.1/pdf/). 

# Flask migrate
Setting up flask migrate took a bit. This was helpful. 
* https://blog.miguelgrinberg.com/post/how-to-add-flask-migrate-to-an-existing-project

# Flask forms
- https://hackersandslackers.com/flask-wtforms-forms/
- https://flask.palletsprojects.com/en/1.1.x/patterns/wtforms/#the-forms

# Plotly Dash integration
* CSRF issue resolved by this solution https://stackoverflow.com/a/51618986

