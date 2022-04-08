#coding=utf-8
from uliweb import expose, functions, models
from uliweb.i18n import ugettext_lazy as _
from json import loads as json_loads

@expose('/admin/roles')
class RoleView(object):
    def __begin__(self):
        if not (request.user and request.user.is_superuser):
            if request.function.find("api_") != -1:
                return json({"success": False, "msg": "unauthorized"}, status=401)
            error(_('superuser needed'))

    @expose('')
    def list(self):
        role = "ADMIN"
        table = functions.get_apijson_table("role", role=role, tableui_name="roles")
        return {
            "table_json":json_dumps(table.to_dict()),
            "role":role,
        }

    def view(self):
        id_ = request.values.get("id")
        if not id_:
            error(_('No role id'))
        
        role = "ADMIN"
        table = functions.get_apijson_table("role", role=role, tableui_name = "roles")

        Role = models.role
        User = models.user
        role_ = Role.get(id_)
        if not role_:
            error(_('Role "%s" not found'%(id_)))

        users = [i for i in role_.users]
        init_users = [i.id for i in users]
        init_user_labels = ["%s (%s)"%(i.username,i.nickname) for i in users]

        groups = [i for i in role_.usergroups]
        init_groups = [i.id for i in groups]
        init_group_labels = [i.name for i in groups]

        permissions = [i for i in role_.permissions]
        init_permissions = [i.id for i in permissions]
        init_permission_labels = [i.name for i in permissions]


        return {
            "id_":id_,
            "table_json":json_dumps(table.to_dict()),
            "role":role,

            "init_users":json_dumps(init_users),
            "init_user_labels":json_dumps(init_user_labels),

            "init_groups":json_dumps(init_groups),
            "init_group_labels":json_dumps(init_group_labels),

            "init_permissions":json_dumps(init_permissions),
            "init_permission_labels":json_dumps(init_permission_labels),
        }
    
    def api_update_users(self):
        request_data = json_loads(request.data)
        role_id = request_data.get("role")
        if not role_id:
            return json({"success": False, "msg": "no role id"})
        if not isinstance(role_id,int):
            return json({"success": False, "msg": "role id should be int"})
        users = request_data.get("users")
        if not isinstance(users,list):
            return json({"success": False, "msg": "no user list for role"})
        Role = models.role
        User = models.user
        r = Role.get(role_id)
        if not r:
            return json({"success": False, "msg": "cannot found role '%s'"%(role_id)})
        user_objs = []
        for i in users:
            o = User.get(i)
            if not o:
                return json({"success": False, "msg": "cannot found user '%s'"%(i)})
            user_objs.append(o)
        ret = r.users.update(user_objs)
        if ret:
            return json({"success": True, "msg": "update role '%s' successfully"%(r.name)})
        else:
            return json({"success": False, "msg": "fail to update role '%s', maybe no change"%(r.name)})

    def api_update_groups(self):
        request_data = json_loads(request.data)
        role_id = request_data.get("role")
        if not role_id:
            return json({"success": False, "msg": "no role id"})
        if not isinstance(role_id,int):
            return json({"success": False, "msg": "role id should be int"})
        groups = request_data.get("groups")
        if not isinstance(groups,list):
            return json({"success": False, "msg": "no group list for role"})
        Role = models.role
        UserGroup = models.usergroup
        r = Role.get(role_id)
        if not r:
            return json({"success": False, "msg": "cannot found role '%s'"%(role_id)})
        group_objs = []
        for i in groups:
            o = UserGroup.get(i)
            if not o:
                return json({"success": False, "msg": "cannot found group '%s'"%(i)})
            group_objs.append(o)
        ret = r.usergroups.update(group_objs)
        if ret:
            return json({"success": True, "msg": "update role '%s' successfully"%(r.name)})
        else:
            return json({"success": False, "msg": "fail to update role '%s', maybe no change"%(r.name)})

    def api_update_permissions(self):
        request_data = json_loads(request.data)
        role_id = request_data.get("role")
        if not role_id:
            return json({"success": False, "msg": "no role id"})
        if not isinstance(role_id,int):
            return json({"success": False, "msg": "role id should be int"})
        permissions = request_data.get("permissions")
        if not isinstance(permissions,list):
            return json({"success": False, "msg": "no permission list for role"})
        Role = models.role
        Permission = models.permission
        r = Role.get(role_id)
        if not r:
            return json({"success": False, "msg": "cannot found role '%s'"%(role_id)})
        permission_objs = []
        for i in permissions:
            o = Permission.get(i)
            if not o:
                return json({"success": False, "msg": "cannot found permission '%s'"%(i)})
            permission_objs.append(o)
        ret = r.permissions.update(permission_objs)
        if ret:
            return json({"success": True, "msg": "update role '%s' successfully"%(r.name)})
        else:
            return json({"success": False, "msg": "fail to update role '%s', maybe no change"%(r.name)})

@expose('/admin/permissions')
class PermissionView(object):
    def __begin__(self):
        if not (request.user and request.user.is_superuser):
            error(_('superuser needed'))

    @expose('')
    def list(self):
        role = "ADMIN"
        table = functions.get_apijson_table("permission", role=role, tableui_name="permissions")
        return {
            "table_json":json_dumps(table.to_dict()),
            "role":role,
        }
    
    def view(self):
        id_ = request.values.get("id")
        if not id_:
            error(_('No permission id'))
        role = "ADMIN"
        table = functions.get_apijson_table("permission", role=role, tableui_name="permissions")

        Permission = models.permission
        Role = models.role
        perm = Permission.get(id_)
        if not perm:
            error(_('Permission "%s" not found'%(id_)))

        roles = [i for i in perm.perm_roles.all()]
        init_roles = [i.id for i in roles]
        init_role_labels = [i.name for i in roles]

        return {
            "id_":id_,
            "table_json":json_dumps(table.to_dict()),
            "role":role,

            "init_roles":json_dumps(init_roles),
            "init_role_labels":json_dumps(init_role_labels),
        }

    def api_update_roles(self):
        request_data = json_loads(request.data)
        perm_id = request_data.get("permission")
        if not perm_id:
            return json({"success": False, "msg": "no role id"})
        if not isinstance(perm_id,int):
            return json({"success": False, "msg": "role id should be int"})
        roles = request_data.get("roles")
        if not isinstance(roles,list):
            return json({"success": False, "msg": "no role list for role"})
        Role = models.role
        Permission = models.permission
        perm = Permission.get(perm_id)
        if not perm:
            return json({"success": False, "msg": "cannot found role '%s'"%(perm_id)})
        role_objs = []
        for i in roles:
            o = Role.get(i)
            if not o:
                return json({"success": False, "msg": "cannot found role '%s'"%(i)})
            role_objs.append(o)
        ret = perm.perm_roles.update(role_objs)
        if ret:
            return json({"success": True, "msg": "update permission '%s' successfully"%(perm.name)})
        else:
            return json({"success": False, "msg": "fail to update permission '%s', maybe no change"%(perm.name)})
