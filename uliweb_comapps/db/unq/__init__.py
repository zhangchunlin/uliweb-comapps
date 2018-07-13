
def get_unqlite(path = None, name = "default"):
    from uliweb import settings
    from unqlite import UnQLite
    if path:
        return UnQLite(path)
    else:
        return UnQLite(settings.UNQLITE_DB_NAMES.get(name))
