"""Application entry point."""
from main import create_app


def app():
    return create_app()


if __name__ == "__main__":
    app().run(host='0.0.0.0', debug=True)
