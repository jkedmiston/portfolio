# Summary
Portfolio (WIP) 
* [url](https://jke-portfolio.herokuapp.com)

# Heroku setup
* `heroku stack:set container --app jke-portfolio`
* ssh

# Development procedure
* `docker-compose run --rm -p 5000:5000 web python3 -m pdb wsgi.py`