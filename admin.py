#! /usr/env/python
from flask.ext.login import current_user, current_app
from flask.ext.admin import Admin, AdminIndexView
from flask.ext.admin.contrib.peewee import ModelView

from data_model import User, Role, UserRoles, Market

# admin
class AuthMixin(object):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return current_app.login_manager.unauthorized()

class MyAdminIndexView(AuthMixin, AdminIndexView):
    pass

class BaseAdmin(AuthMixin, ModelView):
    pass

class UserAdmin(BaseAdmin):
    column_exclude_list = ['password']

class RoleAdmin(BaseAdmin):
    pass

class UserRolesAdmin(BaseAdmin):
    pass

class MarketAdmin(BaseAdmin):
    pass

def build_admin(app):
    admin = Admin(app, name='Pythia admin', index_view=MyAdminIndexView())
    admin.add_view(UserAdmin(User))
    admin.add_view(RoleAdmin(Role))
    admin.add_view(UserRolesAdmin(UserRoles))
    admin.add_view(MarketAdmin(Market))

    return admin

