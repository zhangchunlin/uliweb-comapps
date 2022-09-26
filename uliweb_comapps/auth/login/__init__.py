
from uliweb import request, json, functions, error
from uliweb.core.SimpleFrame import RedirectException


def redirect_login(next=None):
    from uliweb import Redirect, url_for
    Redirect(next or url_for('uliweb_comapps.auth.login.views.login',
                             next=functions.request_url()))


class JsonErrorException(RedirectException):
    def __init__(self, jdata, code=401):
        self.response = json(jdata, status=code)


def check_access(require_user=True, no_user_jdata=None, no_user_code=401,
                 require_role=None, no_role_jdata=None, no_role_code=403, no_role_err=None,
                 require_perm=None, no_perm_jdata=None, no_perm_code=403, no_perm_err=None):
    is_xhr = request.is_xhr or request.function.find("api_") != -1
    if require_user and not request.user:
        if is_xhr:
            raise JsonErrorException(
                no_user_jdata or {"success": False, "msg": "unauthorized"}, no_user_code)
        else:
            redirect_login()
    if require_role and not functions.has_role(request.user, require_role):
        if is_xhr:
            raise JsonErrorException(
                no_role_jdata or {"success": False, "msg": "not having required role"}, no_role_code)
        else:
            error(no_role_err or "not having required role")
    if require_perm and not functions.has_permission(request.user, require_perm):
        if is_xhr:
            raise JsonErrorException(
                no_perm_jdata or {"success": False, "msg": "no permission"}, no_perm_code)
        else:
            error(no_perm_err or "no permission")
