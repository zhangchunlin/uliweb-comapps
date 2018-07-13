
class _v(object):
    mem_unqlite = None

def get_unqlite(path = None, name = "default"):
    from uliweb import settings
    from unqlite import UnQLite
    if not path:
        path = settings.UNQLITE_DB_NAMES.get(name)
    if path==':mem:':
        #always use a same unqlite of ':mem:'
        if not _v.mem_unqlite:
            _v.mem_unqlite = UnQLite(path)
        return _v.mem_unqlite
    return UnQLite(path)
