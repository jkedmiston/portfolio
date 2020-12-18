from flask_admin import BaseView
from flask_admin.contrib.sqla import ModelView
from extensions import db

class GenericView:
    def __init__(self, table):
        self.table = table

    @classmethod
    def generate(cls,table, name, category=None, fkeys=[], can_delete_item=False, custom_column_formatters=None, custom_column_editable_list=None, endpoint=None, post_creation_funcs=None, cols=[], column_default_sort_in=('id', True)):
        class View(ModelView, BaseView):
            column_display_pk = True
            can_export=True
            can_create=True
            can_delete=can_delete_item
            can_edit=True
            column_list = list(table.__table__.c.keys()) + fkeys + cols
            if column_default_sort_in == ('id', True):
                if 'id' not in column_list:
                    pass
                else:
                    column_default_sort = column_default_sort_in

            column_filters = []
            for k in list(table.__table__.c.keys()):
                if table.__table__.c[k].type.__repr__() == "JSON()":
                    continue
                column_filters.append(k)

            column_filters.extend(fkeys)

            if custom_column_formatters is not None:
                column_formatters = custom_column_formatters.copy()

            if custom_column_editable_list is not None:
                column_editable_list = custom_column_editable_list[:]

            edit_template = 'rule_edit.html'

        if endpoint is None:
            endpoint = name.lower()

        return View(table, db.session, name, category=category, endpoint=endpoint)
