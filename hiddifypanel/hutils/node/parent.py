from flask import g
from flask_babel import lazy_gettext as _
from typing import List


from hiddifypanel.models import Child, AdminUser, ConfigEnum, Domain, ChildMode, hconfig, get_panel_link
from hiddifypanel import hutils
from .api_client import NodeApiClient, NodeApiErrorSchema
from hiddifypanel.panel.commercial.restapi.v2.child.schema import RegisterWithParentInputSchema


def request_childs_to_sync():
    for c in Child.query.filter(Child.id != 0).all():
        if not request_child_to_sync(c):
            hutils.flask.flash(f'{c.name}: '+_('parent.sync-req-failed'), 'danger')


def request_child_to_sync(child: Child) -> bool:
    '''Requests to a child to sync itself with the current panel'''
    child_domain = get_panel_link(child.id)
    if not child_domain:
        return False

    child_admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin, child.id)
    base_url = f'https://{child_domain}/{child_admin_proxy_path}'
    path = '/api/v2/child/sync-parent/'
    res = NodeApiClient(base_url).post(path, payload=None, output=dict)
    if isinstance(res, NodeApiErrorSchema):
        # TODO: log error
        return False
    if res['msg'] == 'ok':
        return True

    return False
# before using this function should check child version


def request_chlid_to_register(name: str, mode: ChildMode, child_link: str, apikey: str) -> bool:
    '''Requests to a child to register itself with the current panel'''
    if not child_link or not apikey:
        return False
    domain = get_panel_link()
    if not domain:
        return False
    from hiddifypanel.panel import hiddify

    payload = RegisterWithParentInputSchema()
    payload.parent_panel = hiddify.get_account_panel_link(AdminUser.by_uuid(g.account.uuid), domain.domain)  # type: ignore
    payload.parent_unique_id, payload.name = hconfig(ConfigEnum.unique_id)

    res = NodeApiClient(child_link, apikey).post('/api/v2/child/register-parent/', payload, dict)

    if isinstance(res, NodeApiErrorSchema):
        # TODO: log error
        return False
    if res['msg'] == 'ok':
        return True

    return False


def is_child_domain_active(child: Child, domain: Domain) -> bool:
    '''Checks whether a child's domain is responsive'''
    if not domain.need_valid_ssl:
        return False
    api_key = g.account.uuid
    child_admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin, child.id)
    if not api_key or not child_admin_proxy_path:
        return False

    return hutils.node.is_panel_active(domain.domain, child_admin_proxy_path, api_key)


def get_child_active_domains(child: Child) -> List[Domain]:
    actives = []
    for d in child.domains:
        if is_child_domain_active(child, d):
            actives.append(d)
    return actives


def is_child_active(child: Child) -> bool:
    for d in child.domains:
        if is_child_domain_active(child, d):
            return True
    return False
