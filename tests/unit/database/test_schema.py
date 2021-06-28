from extensions import db
from database.schema import ExampleData, PickleRank, Vendor
import pandas as pd


def test_example_data(app):
    with app.test_request_context():
        e = ExampleData(alias="test")
        db.session.add(e)
        db.session.commit()
        print(len(ExampleData.query.all()))


def test_pickle_schema(app):
    with app.test_request_context():
        v = Vendor(name="Target", url="www.target.com")
        db.session.add(v)
        db.session.commit()

        p = PickleRank(price=8.1, votes=1, product_url="www.product.com",
                       product_description="Wonderful texture")
        db.session.add(p)
        db.session.commit()

        p.vendors.append(v)
        db.session.commit()

        df = pd.read_sql("select * from vendors", con=db.engine)
        dg = pd.read_sql("select * from pickles", con=db.engine)
        dh = pd.read_sql("select * from pickle_vendor", con=db.engine)
        import pdb
        pdb.set_trace()
        print("done")
