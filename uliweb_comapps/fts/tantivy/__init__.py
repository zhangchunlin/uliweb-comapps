def get_tantivy(name = "default", path = None, schema = None):
    '''get a tantivy object
    :param name: use name to get a tantivy object, lookup in settings.TANTIVY_INDEX
    :param path: index directory path, if None, will use configuration get from name
    :param schema: index schema, if None, will use configuration from name
    '''
    import tantivy
    from uliweb import settings

    c = None
    if not path:
        if not c:
            c = settings.TANTIVY_INDEX.get(name)
        path = c.get("path")
    if not schema:
        if not c:
            c = settings.TANTIVY_INDEX.get(name)
        builder = tantivy.SchemaBuilder()
        for field in c.get("fields"):
            name = field.get("name")
            ftype = field.get("type","text")
            func_name = "add_%s_field"%(ftype)
            func = getattr(builder,func_name)
            stored = field.get("stored",False)
            func(name, stored=stored)

    schema = builder.build()

    index = tantivy.Index(schema,path)
    return index
