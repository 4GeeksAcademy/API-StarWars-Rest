# src/admin.py
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import db, User, People, Planet, Favorite

def setup_admin(app):
    admin = Admin(app, name="Admin", template_mode="bootstrap4")

    class ReadWriteModelView(ModelView):
        column_exclude_list = ("password",)
        form_excluded_columns = ("favorites",)
        can_view_details = True
        create_modal = True
        edit_modal = True

    admin.add_view(ReadWriteModelView(User, db.session, category="Models"))
    admin.add_view(ReadWriteModelView(People, db.session, category="Models"))
    admin.add_view(ReadWriteModelView(Planet, db.session, category="Models"))
    admin.add_view(ReadWriteModelView(Favorite, db.session, category="Models"))
