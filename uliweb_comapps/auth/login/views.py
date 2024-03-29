#coding=utf8

from uliweb.core.SimpleFrame import functions, expose, redirect
from uliweb.i18n import ugettext_lazy as _
from uliweb.utils._compat import import_

unquote = import_('urllib.parse', 'unquote')


def add_prefix(url):
    from uliweb import settings
    return settings.DOMAINS.static.get('url_prefix', '') + url or '/'


def get_request_next():
    from uliweb import request
    next = request.values.get('next')
    if not next:
        next = add_prefix('/')
    return next


def login():
    from uliweb.contrib.auth import login

    form = functions.get_form('auth.LoginForm')()

    if request.user:
        next = request.values.get('next')
        if next:
            return redirect(next)

    next = functions.get_request_next()
    if request.method == 'GET':
        form.next.data = next
        return {'next': next}
    if request.method == 'POST':
        flag = form.validate(request.values)
        if flag:
            username = form.username.data.strip()
            f, d = functions.authenticate(username=username, password=form.password.data)
            if f:
                request.session.remember = form.rememberme.data
                login(username)
                next = unquote(next)
                return redirect(next)
            else:
                form.errors.update(d)
        #request.is_xhr is deprecated in new werkezeug
        #https://stackoverflow.com/questions/60131900/weird-is-xhr-error-when-deploying-flask-app-to-heroku
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return json({'success': False, '_': 'Login Failed', 'errors': form.errors})
        else:
            msg = form.errors.get('_', '') or _('Login failed!')
            return {'form': form, 'msg': str(msg)}

@expose("/api_login")
def api_login():
    from uliweb.contrib.auth import login

    relogin = request.POST.get("relogin", "") == "true"
    session_as_token = request.POST.get("session_as_token", "") == "true"

    def _result_json():
        if session_as_token:
            return json({"success": True,
                        "msg": "Login success.",
                        "token": request.session.key,
                        "expiry_time": request.session.expiry_time})
        return json({"success": True, "msg": "Login success."})

    if request.user and not relogin:
        return _result_json()

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    rememberme = request.POST.get("rememberme", "") == "true"

    if not username or not password:
        return json({"success": False, "msg": "Empty username or password."})

    f, d = functions.authenticate(username=username, password=password)
    if f:
        request.session.remember = rememberme
        login(username)

        return _result_json()
    else:
        return json({"success": False, "msg": "User does not exist or password is not correct!"})

def register():
    from uliweb import settings
    from uliweb.contrib.auth import create_user, login

    if not settings.LOGIN.register:
        error('不允许用户自行注册')

    next = request.values.get('next')
    if not next:
        next = request.referrer
        if not next or (next and next.endswith('/register')):
            next = add_prefix('/')

    form = functions.get_form('auth.RegisterForm')()

    if request.method == 'GET':
        form.next.data = next
        return {'form': form, 'msg': ''}
    if request.method == 'POST':
        flag = form.validate(request.values)
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

        if request.is_xhr:
            return json({'success': False, '_': 'Register Failed', 'errors': form.errors})
        else:
            msg = form.errors.get('_', '') or _('Register failed!')
            return {'form': form, 'msg': str(msg)}

def logout():
    from uliweb.contrib.auth import logout as out
    from uliweb import settings
    out()
    next = unquote(request.POST.get('next', add_prefix('/')))
    return redirect(next)
