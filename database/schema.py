from extensions import db
from sqlalchemy_utils import URLType, EmailType, UUIDType


class ReportResult(db.Model):
    __tablename__ = "report_results"
    user_email = db.Column(EmailType)
    service_email = db.Column(EmailType)
    slides_url = db.Column(URLType)
    unique_tag = db.Column(UUIDType(binary=False))


class ExampleData(db.Model):
    __tablename__ = "example_data"
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.Text, nullable=True)


class RandomData(db.Model):
    __tablename__ = "random_data"
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)


class PubSubMessage(db.Model):
    __tablename__ = "pubsub_messages"
    id = db.Column(db.Integer, primary_key=True)
    publish_time = db.Column(db.DateTime, nullable=False)
    unique_tag = db.Column(db.Text)
    data = db.Column(db.JSON, default=lambda: {})
