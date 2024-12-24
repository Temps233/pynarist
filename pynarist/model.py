# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# for more information, see https://github.com/Temps233/pynarist/blob/master/NOTICE.txt
import inspect
from typing import ClassVar, Self, dataclass_transform


from pynarist._errors import UsageError
from pynarist._impls import Implementation, getImpl, registerImpl


@dataclass_transform(kw_only_default=True)
class Model:
    fields: ClassVar[dict[str, type[Implementation]]] = {}

    def __init_subclass__(cls: type[Self]) -> None:
        cls.fields = inspect.get_annotations(cls)

        class Impl:
            __pynarist_redirector__: cls

            def build(self, obj: cls) -> bytes:
                return obj.build()

            def parseWithSize(self, data: bytes) -> tuple[cls, int]:
                return cls.parseWithSize(data)

        registerImpl(cls, Impl())  # type: ignore

    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if key in self.fields:
                setattr(self, key, value)
            else:
                raise UsageError(f"Unknown field: {key}")

    def build(self) -> bytes:
        result = b""
        for key, value in self.fields.items():
            if hasattr(self, key):
                result += getImpl(value).build(getattr(self, key))
        return result

    @classmethod
    def parse(cls, data: bytes) -> Self:
        return cls.parseWithSize(data)[0]

    @classmethod
    def parseWithSize(cls, data: bytes) -> tuple[Self, int]:
        result = {}
        total_size = 0
        for key, value in cls.fields.items():
            impl = getImpl(value)
            result[key], size = impl.parseWithSize(data)
            total_size += size
            data = data[size:]
        return cls(**result), total_size

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(f'{k}={v!r}' for k, v in self.__dict__.items() if k in self.fields)})"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return all(
            getattr(self, key, None) == getattr(other, key, None)
            for key in self.fields
        )
