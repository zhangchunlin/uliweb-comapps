"""
uliweb-comapps db.unq - UnQLite database support

This module provides access to UnQLite embedded database for Uliweb3 ASGI applications.

Usage:
    from uliweb import functions
    db = functions.get_unqlite()  # Get default database
    db = functions.get_unqlite('mem')  # Get in-memory database
    db = functions.get_unqlite(path='/path/to/db.udb')  # Custom path
"""
# coding=utf-8
from unqlite import UnQLite

# Module version
VERSION = '0.2.0'

# Singleton for in-memory database
_mem_unqlite = None


def get_unqlite(name="default", path=None):
    """
    Get UnQLite database object.

    Args:
        name: UnQLite db name, will use the name to get path from settings.UNQLITE_DB_NAMES
        path: UnQLite db file path, if provided, will ignore name parameter

    Returns:
        UnQLite database object

    Example:
        from uliweb import functions

        # Get default database
        db = functions.get_unqlite()

        # Get named database
        db = functions.get_unqlite('mydb')

        # Get in-memory database
        db = functions.get_unqlite('mem')

        # Custom path (ignores name)
        db = functions.get_unqlite(path='/path/to/database.udb')
    """
    from uliweb import settings

    if not path:
        path = settings.UNQLITE_DB_NAMES.get(name)

    if path == ':mem:':
        # Always use the same UnQLite instance for ':mem:'
        global _mem_unqlite
        if not _mem_unqlite:
            _mem_unqlite = UnQLite(path)
        return _mem_unqlite

    return UnQLite(path)
