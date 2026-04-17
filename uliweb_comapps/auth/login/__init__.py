
from uliweb import request, json, functions, error
from uliweb.core.SimpleFrame import RedirectException


def redirect_login(next=None):
    from uliweb import url_for
    from starlette.responses import RedirectResponse

    next_url = next or url_for('uliweb_lapps.auth.login.views.login',
                               next=functions.request_url())
    return RedirectResponse(next_url, status_code=302)


def get_login_url():
    """获取登录页面的 URL"""
    from uliweb import url_for
    return url_for('uliweb_comapps.auth.login.views.login',
                   next=functions.request_url())


class JsonErrorException(RedirectException):
    def __init__(self, jdata, code=401):
        self.response = json(jdata, status=code)


def check_access(require_user=True, no_user_jdata=None, no_user_code=401,
                 require_role=None, no_role_jdata=None, no_role_code=403, no_role_err=None,
                 require_perm=None, no_perm_jdata=None, no_perm_code=403, no_perm_err=None):
    # ASGI 兼容方式判断是否为 AJAX 请求
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.function.find("api_") != -1
    if require_user and not request.user:
        if is_xhr:
            raise JsonErrorException(
                no_user_jdata or {"success": False, "msg": "unauthorized"}, no_user_code)
        else:
            raise RedirectException(get_login_url())
    if require_role:
        if isinstance(require_role, (tuple, list)):
            has_role = functions.has_role(request.user, *require_role)
        else:
            has_role = functions.has_role(request.user, require_role)
        if not has_role:
            if is_xhr:
                raise JsonErrorException(
                    no_role_jdata or {"success": False, "msg": "not having required role"}, no_role_code)
            else:
                error(no_role_err or "not having required role")
    if require_perm:
        if isinstance(require_perm, (tuple, list)):
            has_permission = functions.has_permission(request.user, *require_perm)
        else:
            has_permission = functions.has_permission(request.user, require_perm)
        if not has_permission:
            if is_xhr:
                raise JsonErrorException(
                    no_perm_jdata or {"success": False, "msg": "no permission"}, no_perm_code)
            else:
                error(no_perm_err or "no permission")
