# UnQLite Database Support for Uliweb3

Add support for [UnQLite](https://unqlite.org/) - a fast, lightweight, embedded NoSQL database engine.

## Requirements

- Python 3.7+
- Uliweb3 (ASGI version)
- unqlite package

Install requirements:
```bash
pip install unqlite
```

## Installation

Add to your project's `apps/settings.ini`:

```ini
INSTALLED_APPS = [
    ...
    'uliweb_comapps.db.unq',
]
```

## Configuration

Configure in `apps/settings.ini`:

```ini
[UNQLITE_DB_NAMES]
# Predefined UnQLite database configurations
# Use name as key to reference in get_unqlite(name='key')
default = './database.udb'
mem = ':mem:'
test = './test.udb'
```

## Usage

### Using functions.get_unqlite()

```python
from uliweb import functions

# Get default database
db = functions.get_unqlite()

# Get named database
db = functions.get_unqlite('test')

# Get in-memory database (shared instance)
db = functions.get_unqlite('mem')

# Use custom path (ignores name parameter)
db = functions.get_unqlite(path='/path/to/database.udb')
```

### Using directly

```python
from uliweb_comapps.db.unq import get_unqlite

db = get_unqlite()
```

## UnQLite Basic Operations

```python
from uliweb import functions

db = functions.get_unqlite()

# Store a value
db.store('key', 'value')

# Fetch a value
value = db.fetch('key')

# Delete a value
db.delete('key')

# Check if key exists
exists = db.exists('key')

# Iterate over keys
for key in db.iter_keys():
    print(key)

# Use collections (similar to Redis)
collection = db.collection('users')
collection.store({'name': 'John', 'age': 30})
for doc in collection.all():
    print(doc)
```

## API

### get_unqlite(name="default", path=None)

Get UnQLite database object.

**Parameters:**
- `name` (str): UnQLite db name, will use the name to get path from settings.UNQLITE_DB_NAMES. Default is "default".
- `path` (str): UnQLite db file path, if provided, will ignore name parameter.

**Returns:**
- UnQLite database object

**Examples:**
```python
# Get default database
db = functions.get_unqlite()

# Get named database
db = functions.get_unqlite('mydb')

# Get in-memory database
db = functions.get_unqlite('mem')

# Custom path (ignores name)
db = functions.get_unqlite(path='/path/to/database.udb')
```

## Related Links

1. [UnQLite](https://unqlite.org/) - Official website
2. [unqlite-python](https://github.com/coleifer/unqlite-python) - Python binding on GitHub
3. [Uliweb3](https://github.com/uliweb/uliweb3) - Uliweb framework

## Notes

- The `:mem:` database uses a singleton pattern - the same instance is returned for all calls with path ':mem:'
- For file-based databases, a new instance is created each time
- UnQLite is a purely synchronous library, but works fine in ASGI applications when used in synchronous contexts
