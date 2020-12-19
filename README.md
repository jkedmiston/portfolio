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
Copy `.env.sample` to `.env`. Populate with credentials from a `json` key if exercising the Google integrations (primarily `GOOGLE_APPLICATION_CREDENTIALS`. 
Build and test: 
* `docker-compose build`
* `docker-compose run --rm web python -m pytest`

# Heroku setup
* `heroku stack:set container --app jke-portfolio`

# Development procedure
Starting up the app so that breakpoints are easy to work in: 
* `docker-compose run --rm -p 5000:5000 web python3 -m pdb wsgi.py`

# Flask migrate
Setting up flask migrate took a bit. This was helpful. 
* https://blog.miguelgrinberg.com/post/how-to-add-flask-migrate-to-an-existing-project

# Flask forms
- https://hackersandslackers.com/flask-wtforms-forms/
- https://flask.palletsprojects.com/en/1.1.x/patterns/wtforms/#the-forms

# Plotly Dash integration
* CSRF issue resolved by this solution https://stackoverflow.com/a/51618986

