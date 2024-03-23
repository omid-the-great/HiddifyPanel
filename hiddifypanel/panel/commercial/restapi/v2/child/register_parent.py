from apiflask import abort, fields, Schema
from flask.views import MethodView
from flask import current_app as app

from hiddifypanel.auth import login_required
from hiddifypanel.models import set_hconfig, ConfigEnum, PanelMode, ChildMode
from hiddifypanel.panel import hiddify_api


class RegisterParentSchema(Schema):
    parent_panel = fields.String(required=True, description="The parent panel link")
    parent_panel_unique_id = fields.String(required=True, description="The parent panel unique id (api key)")
    name = fields.String(required=True, description="The child's name in the parent panel")
    mode = fields.Enum(ChildMode, required=True, description="The child's mode in the parent panel")


class RegisterParent(MethodView):
    decorators = [login_required(parent_auth=True)]

    @app.input(RegisterParentSchema, arg_name='data')
    def post(self, data):
        set_hconfig(ConfigEnum.parent_panel, data['parent_panel'])
        set_hconfig(ConfigEnum.parent_unique_id, data['parent_panel_unique_id'])

        if not hiddify_api.register_child_to_parent(data['name'], data['mode']):
            abort(400, "Register failed")

        set_hconfig(ConfigEnum.panel_mode, PanelMode.child)
        return {'status': 200, 'msg': 'ok'}
