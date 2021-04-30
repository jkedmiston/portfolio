from extensions import db
from database.schema import ExampleData


def test_example_data(app):
    with app.test_request_context():
        e = ExampleData(alias="test")
        db.session.add(e)
        db.session.commit()
        print(len(ExampleData.query.all()))
