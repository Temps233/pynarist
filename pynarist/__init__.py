# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# for more information, see https://github.com/Temps233/pynarist/blob/master/NOTICE.txt

"""
# Pynarist
A Python library for parsing and rebuilding binary data structures.

## Usage

```python
from pynarist import Model, varchar

class Person(Model):
    name: varchar
    age: int

john = Person(name=varchar('John'), age=25)

# Output determined by the endianness of the system

assert john.build() == b'\\x04John\\x19\\x00\\x00\\x00'

parsed = Person.parse(b'\\x04John\\x19\\x00\\x00\\x00')

assert parsed.name == 'John'
assert parsed.age == 25
```
"""

__all__ = [
    "Model",
    "long",
    "short",
    "byte",
    "half",
    "double",
    "char",
    "varchar",
    "fixedstring",
    "array",
    "vector",
    "null",
    "ignore",
]

from .model import Model
from ._impls import (
    # placeholder flags
    null,
    ignore,
    # int flags
    long,
    short,
    byte,
    # float flags
    half,
    double,
    # string flags
    char,
    varchar,
    fixedstring,
    # iterable flags
    array,
    vector,
)
