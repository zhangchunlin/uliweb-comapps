# coding=utf-8

from uliweb import request, json, settings, error
from uliweb.core.SimpleFrame import functions, expose, redirect
from uliweb.i18n import ugettext_lazy as _
from uliweb.utils._compat import import_

unquote = import_('urllib.parse', 'unquote')


def add_prefix(url):
    from uliweb import settings
    return settings.DOMAINS.static.get('url_prefix', '') + url or '/'


def get_request_next():
    from uliweb import request
    from html import escape
    # 使用同步方式获取 GET 参数
    params = request.GET
    next = params.get('next')
    if not next:
        next = add_prefix('/')
    else:
        next = escape(next)
    return next


async def login():
    from uliweb.contrib.auth import login

    form = functions.get_form('auth.LoginForm')()

    if request.user:
        params = await request.get_params()
        nxt = params.get('next')
        if nxt:
            return redirect(nxt)

    next = get_request_next()

    if request.method == 'GET':
        form.next.data = next
        return {'next': next}
    if request.method == 'POST':
        params = await request.get_params()
        flag = form.validate(params)
        if flag:
            username = form.username.data.strip()
            f, d = functions.authenticate(
                username=username, password=form.password.data)
            if f:
                request.session.remember = form.rememberme.data
                login(username)
                next = unquote(next)
                return redirect(next)
            else:
                form.errors.update(d)
        is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax_request:
            return json({'success': False, '_': 'Login Failed',
                         'errors': form.errors})
        else:
            msg = form.errors.get('_', '') or _('Login failed!')
            return {'form': form, 'msg': str(msg)}


@expose("/api_login")
async def api_login():
    from uliweb.contrib.auth import login

    params = await request.get_params()
    relogin = params.get("relogin", "") == "true"
    session_as_token = params.get("session_as_token", "") == "true"

    def _result_json():
        if session_as_token:
            return json({"success": True,
                        "msg": "Login success.",
                        "token": request.session.key,
                        "expiry_time": request.session.expiry_time})
        return json({"success": True, "msg": "Login success."})

    if request.user and not relogin:
        return _result_json()

    username = params.get("username", "").strip()
    password = params.get("password", "")
    rememberme = params.get("rememberme", "") == "true"
    verification_code = params.get("verification_code", "")

    if not username or not password:
        return json({"success": False, "msg": "Empty username or password."})

    f, d = functions.authenticate(username=username, password=password)
    if f:
        request.session.remember = rememberme
        login(username)

        return _result_json()
    else:
        return json({"success": False, "msg": "User does not exist or password is not correct!"})

@expose('/register')
async def register():
    from uliweb import settings
    from uliweb.contrib.auth import create_user, login

    if not settings.LOGIN.register:
        error('不允许用户自行注册')

    params = await request.get_params()

    next = params.get('next')
    if not next:
        next = request.referrer
        if not next or (next and next.endswith('/register')):
            next = add_prefix('/')

    form = functions.get_form('auth.RegisterForm')()

    if request.method == 'GET':
        form.next.data = next
        return {'form': form, 'msg': ''}
    if request.method == 'POST':
        flag = form.validate(params)
        if flag:
            from uliweb import settings
            f, d = create_user(username=form.username.data.strip(),
                               password=form.password.data,
                               auth_type=settings.AUTH.AUTH_TYPE_DEFAULT)
            if f:
                # add auto login support 2012/03/23
                login(d)
                next = unquote(next)
                return redirect(next)
            else:
                form.errors.update(d)

        is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax_request:
            return json({'success': False, '_': 'Register Failed',
                         'errors': form.errors})
        else:
            msg = form.errors.get('_', '') or _('Register failed!')
            return {'form': form, 'msg': str(msg)}


async def logout():
    from uliweb.contrib.auth import logout as out
    out()
    params = await request.get_params()
    next = unquote(params.get('next', add_prefix('/')))
    return redirect(next)
