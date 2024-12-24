# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# for more information, see https://github.com/Temps233/pynarist/blob/master/NOTICE.txt

import struct
from typing import Any, Protocol
from collections import UserList, UserString

from pynarist._errors import UsageError
from functools import lru_cache

MISSING = object()


def registerImpl(source: type, impl: "Implementation"):
    if not isinstance(source, type):
        raise UsageError.new("registerImpl() argument 1 source must be a type")

    __pynarist_impls__[source] = impl


def _format_class_name(cls):
    return cls.__module__.replace(".", "/") + "/" + cls.__name__


@lru_cache(maxsize=128)
def getImpl(source) -> "Implementation":
    if not isinstance(source, type):
        raise UsageError.new("getImpl() argument 1 source must be a type")

    if hasattr(source, "__pynarist_redirect__"):
        impl = __pynarist_impls__[source.__pynarist_redirect__]
        impl.__pynarist_redirector__ = source
        return impl

    if source not in __pynarist_impls__:
        raise NotImplementedError(
            f"No implementation found for class `{_format_class_name(source)}'"
        )

    return __pynarist_impls__[source]


__pynarist_impls__: dict[type, "Implementation"] = {}


class long(int):
    """a flag for int64 numbers"""

    pass


class short(int):
    """a flag for int16 numbers"""

    pass


class byte(int):
    """a flag for int8 numbers"""

    pass


class half(float):
    """a flag for float16 numbers"""

    pass


class double(float):
    """a flag for float64 numbers"""

    pass


class char(UserString):
    """
    character flag.
    """

    def __init__(self, seq: object) -> None:
        super().__init__(seq)
        if len(self.data) > 1:
            raise UsageError.new("char data must be of length 1")


class varchar(UserString):
    """
    A smaller and cheaper string which use 1 byte to store the length.
    """

    def __init__(self, seq: object) -> None:
        super().__init__(seq)
        if len(self.data) > 255:
            raise UsageError.new("varchar data must be of length 255 or less")


class fixedstring(UserString):
    """
    A fixed-length string.
    """

    TYPE_LENGTH = MISSING

    def __init__(self, seq: object) -> None:
        super().__init__(seq)
        if self.TYPE_LENGTH is MISSING:
            raise UsageError.new(
                "length of fixed string not specified; use fixedstring[length] instead"
            )

        if len(self.data) != self.TYPE_LENGTH:
            raise UsageError.new(
                f"fixed string data length {len(self.data)} and type length {self.TYPE_LENGTH} not matched"
            )

    def __class_getitem__(cls, length: int) -> type:
        class Subclass(cls):
            TYPE_LENGTH = length
            __pynarist_redirect__ = cls

        return Subclass


class array(UserList):
    """
    A fixed-length array.
    """

    TYPE_LENGTH = MISSING
    TYPE_ELEMENT = MISSING

    def __init__(self, *seq: object) -> None:
        super().__init__(seq)
        if self.TYPE_LENGTH is MISSING:
            raise UsageError.new(
                "length of array not specified; use array[length] instead"
            )

        if len(self.data) != self.TYPE_LENGTH:
            raise UsageError.new(
                f"array data length {len(self.data)} and type length {self.TYPE_LENGTH} not matched"
            )

        if not all(isinstance(x, self.TYPE_ELEMENT) for x in self.data):  # type: ignore
            raise UsageError.new(
                f"array data element type {self.TYPE_ELEMENT} not matched"
            )

    def __class_getitem__(cls, args: tuple[type, int]) -> type:
        dtype, length = args

        class Subclass(cls):
            TYPE_LENGTH = length
            TYPE_ELEMENT = dtype
            __pynarist_redirect__ = cls

        return Subclass


class vector(UserList):
    """
    A variable-length array.
    """

    TYPE_ELEMENT = MISSING

    def __init__(self, *seq: object) -> None:
        super().__init__(seq)
        if not all(isinstance(x, self.TYPE_ELEMENT) for x in self.data):  # type: ignore
            raise UsageError.new(
                f"vector data element type {self.TYPE_ELEMENT} not matched"
            )

    def __class_getitem__(cls, dtype: type) -> type:
        class Subclass(cls):
            TYPE_ELEMENT = dtype
            __pynarist_redirect__ = cls

        return Subclass


class null:
    pass


class ignore:
    pass


class Implementation(Protocol):
    __slots__ = ("__pynarist_redirector__",)
    __pynarist_redirector__: Any

    def build(self, source: Any) -> bytes: ...
    def parse(self, source: bytes) -> Any: ...
    def parseWithSize(self, source: bytes) -> tuple[Any, int]: ...


class ImplNull:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: null

    def build(self, source: null):
        return b"\x00"

    def parse(self, source: bytes) -> None:
        return None

    def parseWithSize(self, source: bytes) -> tuple[None, int]:
        return None, 1


class ImplIgnore:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: ignore

    def build(self, source: ignore):
        return b"\x00"

    def parse(self, source: bytes) -> None:
        return None

    def parseWithSize(self, source: bytes) -> tuple[None, int]:
        return None, len(source)  # ignore all bytes after


class ImplInt:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: int

    def build(self, source: int):
        if source.bit_length() > 32:
            raise UsageError.new(
                "Integer too large to be packed into 4 bytes. Use the long() flag"
            )
        return struct.pack("i", source)

    def parse(self, source: bytes) -> int:
        return struct.unpack_from("i", source)[0]

    def parseWithSize(self, source: bytes) -> tuple[int, int]:
        return struct.unpack_from("i", source)[0], 4


class ImplLong:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: long

    def build(self, source: long):
        if source.bit_length() > 64:
            raise UsageError.new(
                "Long integer too large to be packed into 8 bytes. Use the int() flag"
            )
        return struct.pack("q", source)

    def parse(self, source: bytes) -> int:
        return int(struct.unpack_from("q", source)[0])

    def parseWithSize(self, source: bytes) -> tuple[int, int]:
        return int(struct.unpack_from("q", source)[0]), 8


class ImplShort:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: short

    def build(self, source: short):
        if source.bit_length() > 16:
            raise UsageError.new(
                "Short integer too large to be packed into 2 bytes. Use the int() flag"
            )
        return struct.pack("h", source)

    def parse(self, source: bytes):
        return int(struct.unpack_from("h", source)[0])

    def parseWithSize(self, source: bytes) -> tuple[int, int]:
        return int(struct.unpack_from("h", source)[0]), 2


class ImplByte:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: byte

    def build(self, source: byte):
        if source.bit_length() > 8:
            raise UsageError.new("Byte integer too large to be packed into 1 byte.")
        return struct.pack("b", source)

    def parse(self, source: bytes) -> int:
        return int(struct.unpack_from("b", source)[0])

    def parseWithSize(self, source: bytes) -> tuple[int, int]:
        return int(struct.unpack_from("b", source)[0]), 1


class ImplHalf:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: half

    def build(self, source: half):
        return struct.pack("e", source)

    def parse(self, source: bytes) -> float:
        return struct.unpack_from("e", source)[0]

    def parseWithSize(self, source: bytes) -> tuple[float, int]:
        return struct.unpack_from("e", source)[0], 2


class ImplFloat:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: float

    def build(self, source: float):
        return struct.pack("f", source)

    def parse(self, source: bytes) -> float:
        return struct.unpack_from("f", source)[0]

    def parseWithSize(self, source: bytes) -> tuple[float, int]:
        return struct.unpack_from("f", source)[0], 4


class ImplDouble:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: double

    def build(self, source: double):
        return struct.pack("d", source)

    def parse(self, source: bytes) -> float:
        return struct.unpack_from("d", source)[0]

    def parseWithSize(self, source: bytes) -> tuple[float, int]:
        return struct.unpack_from("d", source)[0], 8


class ImplFixedString:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: fixedstring

    def build(self, source: fixedstring):
        return source.data.encode("utf-8")

    def parse(self, source: bytes) -> str:
        length = self.__pynarist_redirector__.TYPE_LENGTH
        return str(source[:length].decode("utf-8"))

    def parseWithSize(self, source: bytes) -> tuple[str, int]:
        length = self.__pynarist_redirector__.TYPE_LENGTH
        return str(source[:length].decode("utf-8")), length  # type: ignore


class ImplArray:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: array

    def build(self, source: array) -> bytes:
        return b"".join(
            getImpl(self.__pynarist_redirector__.TYPE_ELEMENT).build(x) for x in source
        )

    def parse(self, source: bytes) -> list:
        length = self.__pynarist_redirector__.TYPE_LENGTH
        element_impl = getImpl(self.__pynarist_redirector__.TYPE_ELEMENT)
        result = []
        offset = 0
        for _ in range(length): # type: ignore
            element, size = element_impl.parseWithSize(source[offset:])
            result.append(element)
            offset += size
        return result

    def parseWithSize(self, source: bytes) -> tuple[list, int]:
        length = self.__pynarist_redirector__.TYPE_LENGTH
        element_impl = getImpl(self.__pynarist_redirector__.TYPE_ELEMENT)
        result = []
        offset = 0
        for _ in range(length):  # type: ignore
            element, size = element_impl.parseWithSize(source[offset:])
            result.append(element)
            offset += size
        return result, offset


class ImplVector:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: vector

    def build(self, source: vector) -> bytes:
        encoded = b"".join(
            getImpl(self.__pynarist_redirector__.TYPE_ELEMENT).build(x) for x in source
        )
        return struct.pack("I", len(source)) + encoded

    def parse(self, source: bytes) -> list:
        length = struct.unpack_from("I", source)[0]
        element_impl = getImpl(self.__pynarist_redirector__.TYPE_ELEMENT)
        result = []
        offset = 4
        for _ in range(length):
            element, size = element_impl.parseWithSize(source[offset:])
            result.append(element)
            offset += size
        return result

    def parseWithSize(self, source: bytes) -> tuple[list, int]:
        length = struct.unpack_from("I", source)[0]
        element_impl = getImpl(self.__pynarist_redirector__.TYPE_ELEMENT)
        result = []
        offset = 4
        for _ in range(length):
            print(_)
            element, size = element_impl.parseWithSize(source[offset:])
            result.append(element)
            offset += size
        return result, offset


class ImplVarChar:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: varchar

    def build(self, source: varchar):
        encoded = source.encode("utf-8")
        return struct.pack("B", len(encoded)) + encoded

    def parse(self, source: bytes) -> str:
        length = struct.unpack_from("B", source)[0]
        return str(source[1 : 1 + length].decode("utf-8"))

    def parseWithSize(self, source: bytes) -> tuple[str, int]:
        length = struct.unpack_from("B", source)[0]
        return str(source[1 : 1 + length].decode("utf-8")), 1 + length


class ImplChar:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: char

    def build(self, source: char):
        return source.encode("utf-8")

    def parse(self, source: bytes) -> str:
        return source.decode("utf-8")

    def parseWithSize(self, source: bytes) -> tuple[str, int]:
        return source.decode("utf-8"), 1


class ImplString:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: str

    def build(self, source: str):
        encoded = source.encode("utf-8")
        return struct.pack("I", len(encoded)) + encoded

    def parse(self, source: bytes) -> str:
        length = struct.unpack_from("i", source)[0]
        return str(source[4 : 4 + length].decode("utf-8"))

    def parseWithSize(self, source: bytes) -> tuple[str, int]:
        length = struct.unpack_from("i", source)[0]
        return str(source[4 : 4 + length].decode("utf-8")), 4 + length


class ImplBool:
    __slots__ = ('__pynarist_redirector__',)
    __pynarist_redirector__: bool

    def build(self, source: bool):
        return struct.pack("?", source)

    def parse(self, source: bytes) -> bool:
        return struct.unpack_from("?", source)[0]

    def parseWithSize(self, source: bytes) -> tuple[bool, int]:
        return struct.unpack_from("?", source)[0], 1


registerImpl(null, ImplNull())
registerImpl(ignore, ImplIgnore())
registerImpl(long, ImplLong())
registerImpl(int, ImplInt())
registerImpl(short, ImplShort())
registerImpl(byte, ImplByte())
registerImpl(half, ImplHalf())
registerImpl(float, ImplFloat())
registerImpl(double, ImplDouble())
registerImpl(char, ImplChar())
registerImpl(varchar, ImplVarChar())
registerImpl(fixedstring, ImplFixedString())
registerImpl(str, ImplString())
registerImpl(bool, ImplBool())
registerImpl(array, ImplArray())
registerImpl(vector, ImplVector())
