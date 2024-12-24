import struct
from unittest import TestCase
from pynarist import (
    Model,
    char,
    varchar,
    byte,
    short,
    long,
    double,
    half,
    fixedstring,
    array,
    vector,
)
from pynarist._errors import UsageError
from pynarist._impls import getImpl, registerImpl


class TestImpl(TestCase):
    def test_impl_register(self):
        with self.assertRaises(UsageError):
            registerImpl(
                None,  # type: ignore
                None,  # type: ignore
            )

    def test_impl(self):
        self.assertEqual(getImpl(bool).build(True), struct.pack("?", True))
        self.assertEqual(getImpl(byte).build(127), struct.pack("b", 127))
        self.assertEqual(getImpl(short).build(32767), struct.pack("h", 32767))
        self.assertEqual(getImpl(long).build(6969696969), struct.pack("q", 6969696969))
        self.assertEqual(getImpl(int).build(1), struct.pack("i", 1))

        self.assertEqual(getImpl(half).build(1.0), struct.pack("e", 1.0))
        self.assertEqual(getImpl(float).build(1.0), struct.pack("f", 1.0))
        self.assertEqual(getImpl(double).build(1.0), struct.pack("d", 1.0))

        self.assertEqual(getImpl(char).build(char("a")), b"a")
        self.assertEqual(getImpl(str).build("abc"), b"\x03\x00\x00\x00abc")
        self.assertEqual(getImpl(varchar).build(varchar("hello")), b"\x05hello")
        self.assertEqual(
            getImpl(fixedstring[10]).build(fixedstring[5]("Hello")), b"Hello"
        )

        self.assertEqual(
            getImpl(array[varchar, 3]).build(
                array[varchar, 3](varchar("hello"), varchar("world"), varchar("!")),
            ),
            b"\x05hello\x05world\x01!",
        )
        self.assertEqual(
            getImpl(vector[varchar]).build(
                vector[varchar](varchar("hello"), varchar("world")),
            ),
            b"\x02\x00\x00\x00\x05hello\x05world",
        )

    def test_model_registerImpl(self):
        class Person(Model):
            name: str
            age: int

        getImpl(Person)

    def test_error(self):
        with self.assertRaises(struct.error):
            getImpl(short).parse(b"1")

        with self.assertRaises(AttributeError):
            getImpl(byte).build("123")

        with self.assertRaises(AttributeError):
            getImpl(str).build(123)
