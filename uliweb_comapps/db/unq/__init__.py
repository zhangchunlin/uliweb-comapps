
class _v(object):
    mem_unqlite = None

def get_unqlite(name = "default", path = None):
    '''Get unqlite object
    
    :param name: unqlite db name, will use the name to get path from settings.UNQLITE_DB_NAMES
    :param path: unqlite db file path, if None, will use configuration in get from name
    '''
    
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
