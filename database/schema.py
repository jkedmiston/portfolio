from extensions import db


class ExampleData(db.Model):
    __tablename__ = "example_data"
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.Text, nullable=True)


class RandomData(db.Model):
    __tablename__ = "random_data"
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
