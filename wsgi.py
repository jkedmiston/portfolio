"""Application entry point."""
from main import create_app


# The application was initially being initialized implicitly when this script
# was imported and that was causing problems in the test environment.
# (SQLALCHEMY_DATABASE_URI was never reset by test harness.)
def app():
    return create_app()


if __name__ == "__main__":
    app().run(host='0.0.0.0', debug=True)
