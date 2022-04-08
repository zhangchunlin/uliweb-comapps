#coding=utf-8
from uliweb import expose, functions, models
from uliweb.i18n import ugettext_lazy as _

def _get_portrait_image_filename(id):
    import os
    return os.path.join('portraits', str(id) + '.tmp' + '.jpg')

def _get_portrait_image_thumbnail(id, size=50):
    import os
    return os.path.join('portraits', str(id) + '.%dx%d' % (size, size) + '.jpg')

def get_user_image(user, size=50):
    from uliweb import functions
    import os
    
    if user:
        image = functions.get_filename(_get_portrait_image_thumbnail(user.id, size))
        if os.path.exists(image):
            image_url = functions.get_href(_get_portrait_image_thumbnail(user.id, size))
            return image_url

    return functions.url_for_static('images/user%dx%d.jpg' % (size, size))

_timezone_options = []
def get_timezone_options():
    global _timezone_options
    if _timezone_options:
        return _timezone_options
    else:
        from pendulum import timezones, from_timestamp
        def _get_label(t):
            offset = from_timestamp(0, t).offset_hours
            sign = "+" if (offset>=0) else "-"
            offset = abs(offset)
            i = int(offset)
            f = offset -i
            return "%s [%s%02d:%02d]"%(t,sign,i,int(f*60+0.5))
        _timezone_options = []
        for i in timezones:
            try:
                _timezone_options.append({"value":i,"label":_get_label(i)})
            except Exception:
                pass
        return _timezone_options

@expose('/user')
class UserView(object):
    def __begin__(self):
        functions.require_login()

    def view(self):
        user = request.user
        if not user:
            error(_('User is not exists!'))
        User = models.user
        UserGroup = models.usergroup
        can_modify = True
        image_url = functions.get_user_image(user)

        role = "OWNER"
        table = functions.get_apijson_table("user", role=role, tableui_name="userself")
        table.tableui["editable"] = can_modify

        return {
            "request_tag":"userself",
            "can_modify":can_modify,
            "image_url":image_url,
            "uid":user.id,
            "table_json":json_dumps(table.to_dict()),
            "role":role,
            "usergroups":list(user.groups.all().order_by('name'))
        }
    
    def edit_image(self):
        from .forms import UploadImageForm
        import os
        from PIL import Image

        file_image = request.files.get('image')
        if file_image:
            filename = _get_portrait_image_filename(request.user.id)
            functions.save_file(filename, file_image, replace=True, convert=False)

        image = _get_portrait_image_filename(request.user.id)
        f = functions.get_filename(image)
        if os.path.exists(f):
            url = functions.get_href(image)
            img = Image.open(f)
            template_data = {'image_url':url, 'size':img.size}
        else:
            url = None
            template_data = {'image_url':url, 'size':(0, 0)}

        return template_data

    def save_image(self):
        from uliweb.utils.image import crop_resize
        from uliweb.contrib.upload import get_filename

        x = int(request.POST.get('x'))
        y = int(request.POST.get('y'))
        w = int(request.POST.get('w'))
        h = int(request.POST.get('h'))

        of = get_filename(_get_portrait_image_filename(request.user.id))
        f = get_filename(_get_portrait_image_thumbnail(request.user.id, size=50))
        crop_resize(of, f, x, y, w, h, size=(50, 50))
        f = get_filename(_get_portrait_image_thumbnail(request.user.id, size=20))
        crop_resize(of, f, x, y, w, h, size=(20, 20))
        flash(_('Save portrait successful'))
        return redirect(url_for(UserView.view))

    def change_password(self):
        User = models.user
        user_id = request.GET.get('user_id', None)
        data = {}
        if user_id:
            user = User.get(int(user_id))
            if user:
                data = {'username':user.username}
        from .forms import ChangePasswordForm1, ChangePasswordForm2
        if request.user:
            form = ChangePasswordForm1()
        else:
            form = ChangePasswordForm2(data=data)
        if request.method == 'GET':
            return {'form':form, 'ok':False}
        if request.method == 'POST':
            flag = form.validate(request.POST)
            if flag:
                User = get_model('user')
                if user_id:
                    user = User.get(User.c.username == form.username.data)
                    user.set_password(form.password.data)
                    user.save()
                    flash(_('Password saved successfully.'))
                    return redirect('/login?next=/')
                else:
                    request.user.set_password(form.password.data)
                    request.user.save()
                    flash(_('Password saved successfully.'))
                    return {'form':form, 'ok':True}
            else:
                if '_' in form.errors:
                    message = form.errors['_']
                else:
                    message = _('There are something wrong, please fix them.')
                flash(message, 'error')
                return {'form':form, 'ok':False}

@expose('/admin/users')
class UserAdmin(object):
    def __begin__(self):
        functions.require_login()
        if not request.user.is_superuser:
            error(_('error: superuser role needed!'))

    def list(self):
        role = "ADMIN"
        table = functions.get_apijson_table("user", role=role, tableui_name = "users")
        return {
            "table_json":json_dumps(table.to_dict()),
            "role":role,
        }
    
    def view(self):
        uid = request.values.get("id")
        if not uid:
            error(_('No user id'))
        User = models.user
        UserGroup = models.usergroup
        user = User.get(int(uid))
        if not user:
            error(_('User is not exists!'))

        can_modify = user.id == request.user.id
        image_url = functions.get_user_image(user)

        role = "ADMIN"
        table = functions.get_apijson_table("user", role=role, tableui_name = "users")
        return {
            "can_modify":can_modify,
            "image_url":image_url,
            "uid":uid,
            "table_json":json_dumps(table.to_dict()),
            "role":role,
            "usergroups":list(user.groups.all().order_by('name'))
        }

@expose('/resign')
def resign():
    from uliweb.contrib.auth import logout
    logout()
    return redirect(url_for('login', next=request.referrer or '/'))
