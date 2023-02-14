# coding=utf-8
from json import loads as json_loads
from uliweb import expose, functions, request, json, settings, json_dumps
from uliweb_comapps.auth.login import JsonErrorException


@expose('/codemo')
class Codemo(object):
    def uliweb_crud(self):
        return {
            "models_json": json_dumps([i for i in settings.MODELS])
        }

    def api_get_query_codemo(self):
        table_type = request.values.get("table_type")
        if table_type == "bootstraptable":
            return self._get_bootstraptable_query_codemo()
        elif table_type == "iviewtable":
            return self._get_iviewtable_query_codemo()
    
    def _get_bootstraptable_query_codemo(self):
        model_name = request.values.get("model")
        if not model_name:
            return json({"success": False, "msg": "model not given"})
        model = functions.get_model(model_name)
        self.table_url_for_prefix = request.values.get(
            "table_url_for_prefix", "PROJECT.APP.views.CLASS")
        columns = request.values.get("columns")
        if not columns:
            return json({"success": False, "msg": "columns not given"})
        columns = json_loads(columns)

        column_list = [c["name"] for c in model.get_columns_info()]

        code = '''\
    def api_query_{mname}(self):
        # bootstraptable parameter
        params = json_loads(request.data)
        offset = params.get("offset")
        limit = params.get("limit")
        sort_key = params.get("sort")
        sort_order = params.get("order")
        filters = params.get("filters")

        # query by filter parameter
        model = models.{mname}
        q = model.all()

        # only show not deleted
        if getattr(model, "deleted", None):
            q = q.filter(model.c.deleted!=True)

        # filters
        if filters:
            filters = json_loads(filters)
            columns = set({column_list})
            for k in filters:
                if k in columns:
                    v = filters.get(k)
                    if v:
                        q = q.filter(getattr(model.c, k) == v)

        # get total count
        total = q.count()

        # sort
        if sort_key and sort_order:
            if sort_order not in ("asc", "desc"):
                sort_order = "asc"
            if sort_key in {column_list}:
                c = getattr(model.c, sort_key)
                q = q.order_by(getattr(c, sort_order)())

        # offset & limit
        q = q.offset(offset)
        q = q.limit(limit)
        def _get_info(i):
            d = i.to_dict()
            return d
        rows = [_get_info(i) for i in q]
        return json({{"rows": rows, "total": total}})
'''.format(mname=model_name, column_list= column_list)
        self.table_columns = [c for c in self._get_columns(model, columns, include_id=True)]
        return json({"success": True, "api_query_code": code, "table_ui_code": self._gen_code_bootstraptable_ui(model_name)})

    def _get_iviewtable_query_codemo(self):
        model_name = request.values.get("model")
        if not model_name:
            return json({"success": False, "msg": "model not given"})
        model = functions.get_model(model_name)
        self.table_url_for_prefix = request.values.get(
            "table_url_for_prefix", "PROJECT.APP.views.CLASS")
        columns = request.values.get("columns")
        if not columns:
            return json({"success": False, "msg": "columns not given"})
        columns = json_loads(columns)

        code = '''\
    def api_query_{mname}(self):
'''.format(mname=model_name)
        code += '''\
        # page & sort
        page_size = int(request.values.get("page_size", 10))
        current = int(request.values.get("current", 1))
        sort_key = request.values.get("sort_key")
        sort_order = request.values.get("sort_order")
'''
        code += '''
        # filter parameter'''
        columns_to_filter = []
        for c in self._get_columns(model, columns, ignore_id=True):
            _code = self._gen_code_get_column_from_request(c)
            if _code:
                columns_to_filter.append(c)
                code += _code

        code += '''

        # query by filter parameter
        model = models.{}
        q = model.all()
'''.format(model_name)

        for c in columns_to_filter:
            _code = self._gen_code_query_filter(c)
            if _code:
                code += _code

        clist = [c["name"] for c in model.get_columns_info()]
        code += '''
        # get total count
        total = q.count()
        # sort
        if sort_key and sort_order:
            if sort_order not in ("asc", "desc"):
                sort_order = "asc"
            if sort_key in {clist}:
                c = getattr(model.c, sort_key)
                q = q.order_by(getattr(c, sort_order)())
'''.format(clist=repr(clist))
        code += '''
        # offset & limit
        q = q.offset((current-1)*page_size)
        q = q.limit(page_size)
        def _get_info(i):
            d = i.to_dict()
            return d
        rows = [_get_info(i) for i in q]
        return json({"rows": rows, "total": total})
'''
        self.table_columns = [c for c in self._get_columns(model, columns, include_id=True)]
        return json({"success": True, "api_query_code": code, "table_ui_code": self._gen_code_iviewtable_ui(model_name)})

    def _gen_code_get_column_from_request(self, c, source_vname="request.values"):
        t, cname, vname = self._get_column_info(c)
        if t == "INTEGER":
            return '''
        {vname} = int({source_vname}.get("{cname}") or 0)'''.format(source_vname=source_vname, vname=vname, cname=cname)
        elif t == "VARCHAR":
            return '''
        {vname} = {source_vname}.get("{cname}")'''.format(source_vname=source_vname, vname=vname, cname=cname)
        elif t == "DATETIME":
            return '''
        {vname} = {source_vname}.get("{cname}")
        if {vname}:
            try:
                {vname} = pendulum.from_format({vname}, 'YYYY-MM-DD HH:mm:ss', 'Asia/Shanghai')
            except:
                {vname} = None\
'''.format(source_vname=source_vname, vname=vname, cname=cname)
        elif t == "BOOL":
            return '''
        {vname} = {source_vname}.get("{cname}") == "true"'''.format(source_vname=source_vname, vname=vname, cname=cname)

    def _gen_code_query_filter(self, c):
        t, cname, vname = self._get_column_info(c)
        code = ""
        if t in ["INTEGER", "VARCHAR", "BOOL"]:
            code = '''\
        if {vname}:
            q = q.filter(model.c.{cname} == {vname})
'''.format(vname=vname, cname=cname)
        elif t == "DATETIME":
            code = '''\
        if {vname}:
            # TODO: > or < ?
            q = q.filter(model.c.{cname} > {vname})
'''.format(vname=vname, cname=cname)
        return code

    def _get_column_info(self, c):
        t = c["type"]
        if t == 'Reference':
            t = c["type_name"]
        cname = c["name"]
        if cname == "id":
            vname = "id_"
        else:
            vname = cname
        return t, cname, vname

    def _gen_code_bootstraptable_ui(self, mname):
        columns_code_list = []
        format_code_list = []
        data_choices_code_list = []
        for c in self.table_columns:
            name = c.get("name")
            title = c.get("label") or c.get("verbose_name") or name
            action_code = ""
            if c.get("choices"):
                action_code = ", formatter: this.format_{name}".format(name=name)
                fcode = """\
        format_{name}: function(value, row){{
            var label = ""
            for (var i=0;i<this.choices_{name}.length;i++){{
                if (this.choices_{name}[i].value==row.{name}) {{
                    label = this.choices_{name}[i].label
                }}
            }}
            return '<span>'+label+'</span>'
        }}""".format(name=name, mname=mname)
                format_code_list.append(fcode)
                ccode = '''\
            {{{{model = models.{mname};choices=model.{key}.choices;choices=[{{"label":l, "value":v}} for v,l in choices()]}}}}
            choices_{key}: {{{{=json_dumps(choices)}}}}'''.format(mname=mname, key=name)
                data_choices_code_list.append(ccode)
            code = '''\
                {{title: "{title}", width: 100, field: "{name}", sortable: true{action_code}}}'''.format(title=title, name=name, action_code=action_code)
            columns_code_list.append(code)
        code = '''\
                {title: "Action", width: 100, formatter: this.format_action}'''
        columns_code_list.append(code)
        columns_code = ",\n".join(columns_code_list)
        format_code = ",\n".join(format_code_list)
        if format_code:
            format_code += ",\n"
        data_choices_code = ",\n".join(data_choices_code_list)
        if data_choices_code:
            data_choices_code = "\n" + data_choices_code + ","

        code = """\
<script>
Vue.component('table-{mname}', {{
    delimiters: ['{{', '}}'],
    props: [],
    components: {{'BootstrapTable': BootstrapTable}},
    //add vue_format_mixin for vueFormatter and vueFormatterPostBody, https://blog.bootstrap-table.com/2019/08/10/formatter-use-vue-component/
    mixins: [vue_format_mixin],
    template: `\
<div>
    <bootstrap-table ref="btable_{mname}" :options="options" :columns="columns"></bootstrap-table>
</div>\
`,
    data:function(){{
        var this_ = this
        return {{\
{data_choices_code}
            filters: {{}},
            # https://bootstrap-table.com/docs/api/table-options/
            options: {{
                showRefresh: true,
                showColumns: true,
                showExport: true,
                pagination: true,
                sidePagination: "server",
                pageList: [20, 50, 100, 500, 1000],
                pageSize: "20",
                sortName: "id",
                sortOrder: "desc",
                method: "post",
                deferUrl: "{{{{=url_for('{table_url_for_prefix}.api_query_{mname}')}}}}",
                onPostBody: this.vueFormatterPostBody,
                queryParams: function (params) {{
                    params.filters = JSON.stringify(this_.filters)
                    return params
                }}
            }},
            # https://bootstrap-table.com/docs/api/column-options/
            columns: [
{columns_code}
            ]
        }}
    }},
    methods: {{
        init: function(){{
            this.refresh()
        }},
{format_code}\
        format_action: function(value, row, index, field){{
            var this_ = this
            return this.vueFormatter({{
                template: '<Row><edit-{mname} :id="itemid" :after_edit="refresh_row" style="margin-right: 5px;"></edit-{mname}><remove-{mname} :id="itemid" :after_remove="refresh"></remove-{mname}></Row>',
                computed: {{
                    itemid: function(){{return row.id}}
                }},
                methods: {{
                    refresh_row: function(items){{
                        for (var k in items) {{
                            if (k in row) {{
                                row[k] =  items[k]
                            }}
                        }}
                        this_.refresh_row(index, row)
                    }},
                    refresh: this_.refresh
                }}
            }})
        }},
        refresh_row: function(index, row){{
            this.$refs.btable_{mname}.updateRow({{index: index, row: row}})
        }},
        refresh: function(filters=null){{
            if (filters!=null) {{
                this.filters = filters
            }}
            this.$refs.btable_{mname}.refresh()
        }}
    }},
    mounted: function(){{
        this.$nextTick(function () {{this.init()}})
    }}
}})
</script>
""".format(mname=mname, columns_code=columns_code, format_code=format_code, data_choices_code=data_choices_code, table_url_for_prefix=self.table_url_for_prefix)
        return code

    def _gen_code_iviewtable_ui(self, mname):
        code=""""""
        return code


    def api_get_model_columns(self):
        model_name = request.values.get("model")
        model = functions.get_model(model_name)
        no_id = request.values.get("no_id")
        no_id = (no_id == "true")

        def _get_info(c):
            label = c.get("label") or c.get("verbose_name") or c.get("name")
            t = c["type"]
            if t == 'Reference':
                t = c["type_name"]
            label = "{} ({})".format(label, t)
            name = c.get("name")
            return {"label": label, "name": name}

        columns = [_get_info(c) for c in self._get_columns(model, ignore_id=no_id)]
        return json({"success": True, "columns": columns})

    def api_get_add_codemo(self):
        model_name = request.values.get("model")
        if not model_name:
            return json({"success": False, "msg": "model not given"})
        model = functions.get_model(model_name)
        self.add_url_for_prefix = request.values.get(
            "add_url_for_prefix", "PROJECT.APP.views.CLASS")
        columns = request.values.get("columns")
        if not columns:
            return json({"success": False, "msg": "columns not given"})
        columns = json_loads(columns)

        code = '''\
    def api_addupdate_{mname}(self):
        #get values from request
        _action = request.values.get("_action")
        if _action not in ("add","update"):
            return json({{"success": False, "msg": "bad action: {{}}".format(_action)}})
        items = request.values.get("items")
        if not items:
            return json({{"success": False, "msg": "bad param: no items"}})
        items = json_loads(items)
        try:
            id_ = int(items.get("id"))
        except:
            return json({{"success": False, "msg": "id not a int"}})
        if _action == "add" and id_:
            return json({{"success": False, "msg": "should not include id for adding"}})
        if _action != "add" and not id_:
            return json({{"success": False, "msg": "should include id for update"}})
'''.format(mname=model_name)
        for c in self._get_columns(model, columns, ignore_id=True):
            code += self._gen_code_get_column_value(c)
        params = ", ".join(["{pname}={pname}".format(
            pname=c["name"]) for c in self._get_columns(model, columns, ignore_id=True)])
        code += '''
        model = models.{mname}
        if _action == "add":
            #new object and save to database
            obj = model({params})
            ret = obj.save()
            if not ret or (not obj.id):
                log.error("fail to create new {mname} with {{values}}".format(values = request.values))
                return json({{"success": False, "msg": "fail to add {mname}"}})
            return json({{"success": True, "msg": "Success to add {mname}"}})
        else:
            #get object with id and update
            obj = model.get(id_)
            if not obj:
                json({{"success": False, "msg": "{mname} '{{}}' not found".format(id_)}})
            if getattr(model, "deleted", None):
                if obj.deleted:
                    return json({{"success": False, "msg": "{mname} '{{}}' was deleted, cannot be updated".format(id_)}})
            obj.update({params})
            ret = obj.save()
            if not ret:
                log.error("fail to update {mname} with {{values}}".format(values = request.values))
                return json({{"success": False, "msg": "fail to update {mname} #{{}}, maybe no change".format("id_")}})
            return json({{"success": True, "msg": "Success to update {mname}"}})\
'''.format(mname=model_name, params=params)

        self.add_columns = [c for c in self._get_columns(model, columns, ignore_id=True)]
        self.edit_columns = [c for c in self._get_columns(model, columns, include_id=True)]

        return json({"success": True, "api_add_code": code,
            "add_ui_code": self._gen_code_add_ui(model_name), "edit_ui_code": self._gen_code_edit_ui(model_name)})

    def _get_columns(self, model, columns=None, ignore_id=False, include_id=False):
        nlist = []
        cdict = {}
        first_id = None
        for c in model.get_columns_info():
            name = c["name"]
            field = getattr(model, name)
            choices = getattr(field, "choices")
            if choices:
                c["choices"] = True
            if include_id and name == "id":
                first_id = c
                continue
            if columns:
                if name not in columns:
                    continue
            cdict[name] = c
            nlist.append(name)
        if columns:
            nlist = columns
        if first_id:
            yield first_id
        for name in nlist:
            if ignore_id and name == "id":
                continue
            yield cdict[name]

    def _gen_code_get_column_value(self, c):
        code = ""
        t, cname, vname = self._get_column_info(c)

        _code = self._gen_code_get_column_from_request(c, source_vname="items")
        if _code:
            code += _code
        else:
            return code

        code += '''
        if not {vname}:
            return json({{"success": False, "msg": "bad parameter: no {vname}"}})'''.format(vname=vname)
        return code

    def _gen_code_add_ui(self, mname):
        form_items_code_list = []
        data_items_code_list = []
        data_choices_code_list = []
        init_code_list = []
        t2input = {
            "INTEGER": '''<i-input v-model="items.{key}" type="number"></i-input>''',
            "VARCHAR": '''<i-input v-model="items.{key}"></i-input>''',
            "BOOL": '''<checkbox v-model="items.{key}"></checkbox>''',
            "DATETIME": '''<DatePicker type="datetime" v-model="items.{key}" placeholder="Select date" style="width: 200px" />''',
            "CHOICES": '''<i-select v-model="items.{key}" style="width:200px"><i-option v-for="item in choices_{key}" :value="item.value" :key="item.value">{{ item.label }}</i-option></i-select>''',
        }
        t2default = {
            "INTEGER": '''0''',
            "VARCHAR": '''""''',
            "BOOL": '''false''',
            "DATETIME": '''null''',
            "CHOICES": '''null''',
        }
        for c in self.add_columns:
            label = c["label"] or c["verbose_name"] or c["name"]
            t = c["type"]
            choices = c.get("choices")
            if choices:
                t = "CHOICES"
                code = '''\
            {{{{model = models.{mname};choices=model.{key}.choices;choices=[{{"label":l, "value":v}} for v,l in choices()]}}}}
            choices_{key}: {{{{=json_dumps(choices)}}}}'''.format(mname=mname, key=c["name"])
                data_choices_code_list.append(code)
            if t == "Reference":
                t = "CHOICES"
                code = '''\
            choices_{key}: []'''.format(key=c["name"])
                data_choices_code_list.append(code)
                code = '''\
            $.ajax({{
                type: "POST",
                url: "{{{{=url_for('{add_url_for_prefix}.api_get_{key}')}}}}",
                data: {{_action: "get_list"}},
                success: function (data) {{
                    if (data.success) {{
                        this_.choices_{key} = data.list
                        this_.inited = true
                    }}
                    else {{
                        this_.$Message.error(data.msg)
                        this_.inited = false
                    }}
                }}
            }})'''.format(add_url_for_prefix=self.add_url_for_prefix, key=c["name"])
                init_code_list.append(code)
            input = t2input.get(t, "").format(key=c["name"])
            if not input:
                continue
            code = '''\
            <form-item key="{key}" label="{label}">
                {input_code}
            </form-item>'''.format(key=c["name"], label=label, input_code=input)
            form_items_code_list.append(code)

            default = t2default.get(t, "null")
            code = '''\
                {key}: {default}'''.format(key=c["name"], default=default)
            data_items_code_list.append(code)
        form_items_code = "\n".join(form_items_code_list)
        data_items_code = ",\n".join(data_items_code_list)
        data_choices_code = ",\n".join(data_choices_code_list)
        if data_choices_code:
            data_choices_code = "\n" + data_choices_code + ","
        init_code = ",\n".join(init_code_list)
        if init_code:
            init_code = "            var this_ = this\n" + init_code

        code = '''\
<script>
Vue.component('add-{mname}', {{
    delimiters: ['{{', '}}'],
    props: ['after_add'],
    template: `\
<div>
    <i-button type="primary" @click="add_{mname}">Add</i-button>
    <modal v-model="modal_add_{mname}" title="Add">
        <Spin fix v-if="!inited"></Spin>
        <i-form @submit.native.prevent label-width="150">
{form_items_code}
            <form-item label="Action">
                <i-button type="info" icon="md-create" @click="_add_{mname}">Add</i-button>
            </form-item>
        </i-form>
        <div slot="footer">
            <i-button @click="modal_add_{mname}=false">Cancel</i-button>
        </div>
    </modal>
</div>\
`,
    data: function(){{
        var this_ = this
        return {{
            inited: false,
            modal_add_{mname}: false,\
{data_choices_code}
            items: {{
{data_items_code}
            }}
        }}
    }},
    computed: {{
        fitems: function(){{
            var _fitems = {{}}
            var v
            for (var k in this.items){{
                v = this.items[k]
                if (v instanceof Date) {{
                    v = moment(v).format('YYYY-MM-DD HH:mm:ss')
                }}
                _fitems[k] = v
            }}
            return _fitems
        }}
    }},
    methods: {{
        add_{mname}: function(){{
            this.modal_add_{mname} = true
        }},
        _add_{mname}: function(){{
            var this_ = this
            $.ajax({{
                type: "POST",
                url: "{{{{=url_for('{add_url_for_prefix}.api_addupdate_{mname}')}}}}",
                data: {{
                    _action: "add",
                    items: JSON.stringify(this.fitems)
                }},
                success: function (data) {{
                    if (data.success) {{
                        this_.$Notice.success({{
                            title: 'success to add',
                            desc: data.msg
                        }})
                        this_.modal_add_{mname} = false
                        if (typeof this_.after_add == 'function') {{this_.after_add()}}
                    }}
                    else {{
                        this_.$Notice.error({{
                            title: 'error to add',
                            desc: data.msg
                        }})
                    }}
                }}
            }})
        }},
        init_lazy: function(){{
            if (this.inited) {{
                return
            }}
{init_code}
        }},
        init: function(){{}}
    }},
    mounted: function(){{
        this.$nextTick(function () {{this.init()}})
    }}
}})
</script>
'''.format(mname=mname, form_items_code=form_items_code, data_items_code=data_items_code,
           data_choices_code=data_choices_code, init_code=init_code, add_url_for_prefix=self.add_url_for_prefix)

        return code

    def _gen_code_edit_ui(self, mname):
        form_items_code_list = []
        data_items_code_list = []
        data_choices_code_list = []
        init_code_list = []
        t2input = {
            "INTEGER": '''<i-input v-model="items.{key}" type="number"></i-input>''',
            "VARCHAR": '''<i-input v-model="items.{key}"></i-input>''',
            "BOOL": '''<checkbox v-model="items.{key}"></checkbox>''',
            "DATETIME": '''<DatePicker type="datetime" v-model="items.{key}" placeholder="Select date" style="width: 200px" />''',
            "CHOICES": '''<i-select v-model="items.{key}" style="width:200px"><i-option v-for="item in choices_{key}" :value="item.value" :key="item.value">{{ item.label }}</i-option></i-select>''',
            "id": '''<i-input v-model="items.{key}" readonly></i-input>''',
        }
        t2default = {
            "INTEGER": '''0''',
            "VARCHAR": '''""''',
            "BOOL": '''false''',
            "DATETIME": '''null''',
            "CHOICES": '''null''',
        }
        for c in self.edit_columns:
            label = c["label"] or c["verbose_name"] or c["name"]
            t = c["type"]
            choices = c.get("choices")
            if choices:
                t = "CHOICES"
                code = '''\
            {{{{model = models.{mname};choices=model.{key}.choices;choices=[{{"label":l, "value":v}} for v,l in choices()]}}}}
            choices_{key}: {{{{=json_dumps(choices)}}}}'''.format(mname=mname, key=c["name"])
                data_choices_code_list.append(code)
            if t == "Reference":
                t = "CHOICES"
                code = '''\
            choices_{key}: []'''.format(key=c["name"])
                data_choices_code_list.append(code)
                code = '''\
            $.ajax({{
                type: "POST",
                url: "{{{{=url_for('{add_url_for_prefix}.api_get_{key}')}}}}",
                data: {{_action: "get_list"}},
                success: function (data) {{
                    if (data.success) {{this_.choices_{key} = data.list}}
                    else {{this_.$Message.error(data.msg)}}
                }}
            }})'''.format(add_url_for_prefix=self.add_url_for_prefix, key=c["name"])
                init_code_list.append(code)
            input_type = t
            if c["name"] == "id":
                input_type = "id"
            input = t2input.get(input_type, "").format(key=c["name"])
            if not input:
                continue
            code = '''\
            <form-item key="{key}" label="{label}">
                {input_code}
            </form-item>'''.format(key=c["name"], label=label, input_code=input)
            form_items_code_list.append(code)

            default = t2default.get(t, "null")
            code = '''\
                {key}: {default}'''.format(key=c["name"], default=default)
            data_items_code_list.append(code)
        form_items_code = "\n".join(form_items_code_list)
        data_items_code = ",\n".join(data_items_code_list)
        data_choices_code = ",\n".join(data_choices_code_list)
        if data_choices_code:
            data_choices_code = "\n" + data_choices_code + ","
        init_code = ",\n".join(init_code_list)

        code = '''\
<script>
Vue.component('edit-{mname}', {{
    delimiters: ['{{', '}}'],
    props: ["id", "after_edit"],
    template: `\
<div>
    <i-button type="primary" size-"small" @click="edit_{mname}">Edit</i-button>
    <modal v-model="modal_edit_{mname}" @on-visible-change="on_vchange" title="Edit">
        <Spin fix v-if="loading||!inited"></Spin>
        <i-form @submit.native.prevent label-width="150">
{form_items_code}
            <form-item label="Action">
                <i-button type="info" icon="md-create" @click="_save_{mname}" :loading="updating">Save</i-button>
            </form-item>
        </i-form>
        <div slot="footer">
            <i-button @click="modal_edit_{mname}=false">Cancel</i-button>
        </div>
    </modal>
</div>\
`,
    data: function(){{
        var this_ = this
        return {{
            inited: false,
            loading: false,
            updating: false,
            inited: false,
            modal_edit_{mname}: false,\
{data_choices_code}
            items: {{
{data_items_code}
            }}
        }}
    }},
    computed: {{
        fitems: function(){{
            var _fitems = {{}}
            var v
            for (var k in this.items){{
                v = this.items[k]
                if (v instanceof Date) {{
                    v = moment(v).format('YYYY-MM-DD HH:mm:ss')
                }}
                _fitems[k] = v
            }}
            return _fitems
        }}
    }},
    methods: {{
        edit_{mname}: function(){{
            this.modal_edit_{mname} = true
        }},
        _save_{mname}: function(){{
            var this_ = this
            this.updating = true
            $.ajax({{
                type: "POST",
                url: "{{{{=url_for('{add_url_for_prefix}.api_addupdate_{mname}')}}}}",
                data: {{
                    _action: "update",
                    items: JSON.stringify(this.fitems)
                }},
                success: function (data) {{
                    this_.updating = false
                    if (data.success) {{
                        this_.$Notice.success({{
                            title: 'success to update',
                            desc: data.msg
                        }})
                        this_.modal_edit_{mname} = false
                        if (typeof this_.after_edit == 'function') {{this_.after_edit(this_.fitems)}}
                    }}
                    else {{
                        this_.$Notice.error({{
                            title: 'error to update',
                            desc: data.msg
                        }})
                    }}
                }},
                error: function(xhr, ajaxOptions, thrownError){{
                    this_.updating = false
                }}
            }})
        }},
        on_vchange: function(){{
            if (this.modal_edit_{mname} && (! this.inited)) {{
                this.init()
            }}
        }},
        init: function(){{
            var this_ = this
{init_code}
            this.loading = true
            $.ajax({{
                type: "POST",
                url: "{{{{=url_for('{add_url_for_prefix}.api_get_{mname}')}}}}",
                data: {{
                    _action: "get_one",
                    id: this.id
                }},
                success: function (data) {{
                    this_.loading = false
                    if (data.success) {{
                        for (var k in this_.items) {{
                            this_.items[k] = data.item[k]
                        }}
                        this_.inited = true
                    }}
                    else {{this_.$Message.error(data.msg)}}
                }},
                error: function(xhr, ajaxOptions, thrownError){{
                    this_.loading = false
                }}
            }})
        }}
    }}
}})
</script>
'''.format(mname=mname, form_items_code=form_items_code, data_items_code=data_items_code,
           data_choices_code=data_choices_code, init_code=init_code, add_url_for_prefix=self.add_url_for_prefix)
        return code

    def api_get_get_codemo(self):
        model_name = request.values.get("model")
        if not model_name:
            return json({"success": False, "msg": "model not given"})
        self.get_url_for_prefix = request.values.get(
            "get_url_for_prefix", "PROJECT.APP.views.CLASS")
        code = '''\
    def api_get_{mname}(self):
        # query by filter parameter
        model = models.{mname}
        _action = request.values.get("_action")
        if _action == "get_one":
            try:
                id_ = int(request.values.get("id"))
            except Exception:
                return json({{"success": False, "msg": "bad parameter: no id"}})
            obj = model.get(id_)
            if not obj:
                return json({{"success": False, "msg": "{mname} '{{}}' not found".format(id_)}})
            if getattr(model, "deleted", None):
                if obj.deleted:
                    return json({{"success": False, "msg": "{mname} '{{}}' was deleted".format(id_)}})
            d = obj.to_dict()
            return json({{"success": True, "item": d}})
        elif _action == "get_list":
            q = model.all()
            if getattr(model, "deleted", None):
                q = q.filter(model.c.deleted!=True)
            def _get_info(i):
                d = i.to_dict()
                return d
            rows = [_get_info(i) for i in q]
            return json({{"success": True, "list": rows}})
        else:
            return json({{"success": False, "msg": "bad parameter '_action': {{}}".format(_action)}})
'''.format(mname=model_name)
        return json({"success": True, "api_get_code": code})

    def api_get_remove_codemo(self):
        model_name = request.values.get("model")
        if not model_name:
            return json({"success": False, "msg": "model not given"})
        self.remove_url_for_prefix = request.values.get(
            "remove_url_for_prefix", "PROJECT.APP.views.CLASS")
        code = '''\
    def api_remove_{mname}(self):
        model = models.{mname}
        try:
            id_ = int(request.values.get("id"))
        except Exception:
            return json({{"success": False, "msg": "bad parameter: no id"}})
        obj = model.get(id_)
        if not obj:
            return json({{"success": False, "msg": "{mname} '{{}}' not found".format(id_)}})
        if getattr(model, "deleted", None):
            if obj.deleted:
                return json({{"success": False, "msg": "{mname} '{{}}' was deleted already".format(id_)}})
            obj.deleted = True
            obj.save()
        else:
            obj.delete()
        return json({{"success": True, "msg": "{mname} '{{}}' removed".format(id_)}})
'''.format(mname=model_name)
        return json({"success": True, "api_remove_code": code,
            "remove_ui_code": self._gen_code_remove_ui(model_name)})

    def _gen_code_remove_ui(self, mname):
        code='''\
<script>
Vue.component('remove-{mname}', {{
    delimiters: ['{{', '}}'],
    props: ["id","after_remove"],
    template: `\
<div>
    <i-button type="warning" size="small" @click="remove">Remove</i-button>
    <modal v-model="modal_remove" title="Remove">
        <Spin fix v-if="removing"></Spin>
        Confirm to remove?
        <div slot="footer">
            <i-button @click="_remove" type="warning" :loading="removing">Remove</i-button>
            <i-button @click="modal_remove=false">Cancel</i-button>
        </div>
    </modal>
</div>\
`,
    data: function(){{
        return {{
            modal_remove: false,
            removing: false
        }}
    }},
    methods: {{
        remove: function(){{
            this.modal_remove = true
        }},
        _remove: function(){{
            var this_ = this
            this.removing = true
            $.ajax({{
                type: "POST",
                url: "{{{{=url_for('{remove_url_for_prefix}.api_remove_{mname}')}}}}",
                data: {{
                    id: this.id
                }},
                success: function (data) {{
                    this_.removing = false
                    if (data.success) {{
                        this_.$Notice.success({{
                            title: 'success to remove',
                            desc: data.msg
                        }})
                        this_.modal_remove = false
                        if (typeof this_.after_remove == 'function') {{this_.after_remove()}}
                    }}
                    else {{
                        this_.$Notice.error({{
                            title: 'error to update',
                            desc: data.msg
                        }})
                    }}
                }},
                error: function(xhr, ajaxOptions, thrownError){{
                    this_.removing = false
                }}
            }})
        }}
    }}
}})
</script>
'''.format(mname=mname, remove_url_for_prefix=self.remove_url_for_prefix)
        return code

    def uliweb_app(self):
        return {}

    def api_uliweb_app_codemo(self):
        codemos = {
            "layout": '''{{extend "iview/layout2.html"}}

{{block title}}TITLE{{end title}}

{{block mainmenu_config}}
{{mainmenu_name,mainmenu_active='MAINMENU','MAINMENU_ACTIVE'}}
{{end mainmenu_config}}

{{block sidemenu_config}}
{{sidemenu_name,sidemenu_open,sidemenu_active="SIDEMENU","['MENU_OPEN']","MENU_ACTIVE"}}
{{end sidemenu_config}}

{{block other_use}}
{{use 'ui.vue_router'}}
{{use 'ui.vue_router_cond_sync'}}
{{use 'ui.moment'}}
{{end other_use}}
''',
            "page": '''{{extend "APP/layout.html"}}

{{block sidemenu_config}}
{{sidemenu_name,sidemenu_open,sidemenu_active='SIDEMENU',"['MENU_OPEN']","MENU_ACTIVE"}}
{{end sidemenu_config}}

{{block title}}TITLE{{end title}}

{{block content_main}}
{{end content_main}}

{{block mainapp_vue}}
<script>
    var vm = new Vue({
        el: '#mainapp',
        delimiters: ['{', '}'],
        data: function(){
            return {}
        },
        methods: {},
        computed: {},
        mounted: function(){}
    })
</script>
{{end mainapp_vue}}
''',
            "views": '''# coding=utf-8
import logging
from uliweb import expose, functions, request, settings


log = logging.getLogger('app')


@expose('/app')
class App(object):
    def __begin__(self):
        functions.check_access()

    @expose('')
    def index(self):
        return {}
''',
        }
        return json({"success": True, "codemos": codemos})

    def uliweb_filter(self):
        return {"models_json": json_dumps([i for i in settings.MODELS])}

    def _gen_uliweb_filter_html_codemo(self):
        model_name = request.values.get("model")
        if not model_name:
            raise JsonErrorException({"success": False, "msg": "model not given"}, 200)
        model = functions.get_model(model_name)
        columns = request.values.get("columns")
        if not columns:
            raise JsonErrorException({"success": False, "msg": "columns not given"}, 200)
        columns = json_loads(columns)

        filter_fields_html = ""
        filter_fields_data = ""
        for c in self._get_columns(model, columns):
            filter_fields_html += self._gen_code_filter_html(c)
            filter_fields_data += self._gen_code_columns_init_value(c, ref_options_support=False)

        code = f'''\
<i-form @submit.native.prevent>{filter_fields_html}
</i-form>

<script>
var vm = new Vue({{
    el: '#mainapp',
    delimiters: ['{{', '}}'],
    data: function(){{return {{
        filters:{{{filter_fields_data}
        }}
    }}}},
    method: {{
        update_list: function(){{
            #can use this.filters to filter
        }}
    }}
}})
</script>
'''
        return code

    def _gen_uliweb_filter_component_codemo(self):
        model_name = request.values.get("model")
        if not model_name:
            raise JsonErrorException({"success": False, "msg": "model not given"}, 200)
        model = functions.get_model(model_name)

        column_comp = request.values.get("column_comp")
        if not column_comp:
            return ""
        c = None
        for _c in self._get_columns(model, [column_comp]):
            c = _c
        if not c:
            return ""
        t, cname, vname = self._get_column_info(c)
        
        item_html = ""
        data_fields = ""
        init_func = ""
        if c["type"] == "Reference":
            assert c["relation"][:10] == "Reference("
            m, f = c["relation"][10:-1].split(":")
            mname = m.lower()
            item_html = f"""\
            <i-select :value="value" filterable clearable @on-change="handle_change">
                <i-option v-for="(option, index) in options_{mname}" :value="option.value" :key="index">{{option.label}}</i-option>
            </i-select>"""
            data_fields = f"""
            options_{mname}: [],"""
            init_func = f"""
            var this_ = this
            $.ajax({{
                type: "POST",
                url: "{{{{=url_for('PROJECT.APP.views.CLASS.api_get_{mname}')}}}}",
                data: {{
                    _action: "get_list"
                }},
                success: function (data) {{
                    var items = []
                    for (var i in data.list) {{
                        items.push({{label: data.list[i].label, value: data.list[i].id}})
                    }}
                    this_.options_{mname} = items
                }}
            }})"""
        elif c.get("choices"):
            mname = model_name
            item_html = f"""\
            <i-select :value="value" filterable clearable @on-change="handle_change">
                <i-option v-for="(option, index) in options_{cname}" :value="option.value" :key="index">{{option.label}}</i-option>
            </i-select>"""
            data_fields = f"""
            {{{{model = models.{mname};choices=model.{cname}.choices;choices=[{{"label":l, "value":v}} for v,l in choices()]}}}}
            options_{cname}: {{{{=json_dumps(choices)}}}},"""

        code = f"""\
<script>
Vue.component('filter-{vname}', {{
    delimiters: ['{{', '}}'],
    props: [],
    template: `
        <form-item label="{c['label']}">
{item_html}
        </form-item>
`,
    data: function(){{
        return {{{data_fields}
            value: ""
        }}
    }},
    methods: {{
        init: function(){{{init_func}
        }},
        handle_change: function(v){{
            this.$emit("input", v)
            this.$emit("change", v)
        }}
    }},
    mounted: function(){{
        this.init()
    }}
}})
</script>
"""
        return code

    def api_uliweb_filter_codemo(self):
        codemos = {
            "html_codemo": self._gen_uliweb_filter_html_codemo(),
            "component_codemo": self._gen_uliweb_filter_component_codemo(),
        }
        return json({"success": True, "codemos": codemos})

    def _gen_code_filter_html(self, c):
        t, cname, vname = self._get_column_info(c)
        if c["type"] == "Reference" or c.get("choices"):
            return f'''
    <Row>
        <i-col span="4">
            <filter-{vname} v-model="filters.{vname}" @change="update_list"></filter-{vname}>
        </i-col>
    </Row>'''
        return ""

    def _gen_code_columns_init_value(self, c, ref_options_support=True):
        t, cname, vname = self._get_column_info(c)
        code = f'''
            {vname}: null'''
        return code

    def ajax(self):
        return {}

    def api_ajax_codemo(self):
        codemos = {
            "get":'''\
        $.ajax({
            type: "GET",
            url: "{{=url_for('ULIWEB_PROJECT.APP.views.CLASS.METHOD')}}",
            success: function (data) {
                if (data.success) {}
            }
        })
''',
            "post": '''\
        $.ajax({
            type: "POST",
            url: "{{=url_for('ULIWEB_PROJECT.APP.views.CLASS.METHOD')}}",
            data: {},
            success: function (data) {
                if (data.success) {}
            }
        })
''',
            "post_json": '''\
        var params = {}
        $.ajax({
            type: "POST",
            url: "{{=url_for('ULIWEB_PROJECT.APP.views.CLASS.METHOD')}}",
            contentType: 'application/json',
            data: JSON.stringify(params),
            success: function (data) {
                if (data.success) {}
            }
        })
''',
        }
        return json({"success": True, "codemos": codemos})

    def cli(self):
        return {}

    def api_cli_command(self):
        codemos = {
            "simple_command":'''\
import argparse
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y%m%d%H%M%S')
log = logging.getLogger("cmd")


class Command(object):
    def main(self):
        parser = argparse.ArgumentParser(description='cmd description')
        parser.add_argument('-t', '--test', default=False, action="store_true", help='test help')

        self.args = parser.parse_args()


def main():
    o = Command()
    o.main()


if __name__ == "__main__":
    main()
''',
        }
        return json({"success": True, "codemos": codemos})
