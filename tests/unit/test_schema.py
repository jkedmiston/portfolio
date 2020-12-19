def test_example_data(app):
    from extensions import db
    from database.schema import ExampleData
    with app.test_request_context():
        e = ExampleData(alias="test")
        db.session.add(e)
        db.session.commit()

        assert len(ExampleData.query.all()) == 1
