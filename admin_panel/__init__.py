from flask_admin import AdminIndexView
from admin_panel.generic_view import GenericView
from database.schema import ExampleData, RandomData, PubSubMessage, Healthcheck
from flask_admin import Admin


def add_admin_app(app):
    table_views = [GenericView.generate(
        ExampleData, "ExampleData", "LIMS", can_delete_item=True),
        GenericView.generate(
            RandomData, "RandomData", "Examples", can_delete_item=True),
        GenericView.generate(Healthcheck, "Healthcheck",
                             "Examples", can_delete_item=False),
    ]
    admin = Admin(app, name="Admin", template_mode="bootstrap3",
                  index_view=AdminIndexView())
    admin.add_views(*table_views)
