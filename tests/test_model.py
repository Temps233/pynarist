# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# for more information, see https://github.com/Temps233/pynarist/blob/master/NOTICE.txt
from unittest import TestCase
from pynarist import Model, char, long, byte
from pynarist._errors import UsageError
from pynarist._impls import varchar


class TestModel(TestCase):
    def test_unknown_field(self):
        class A(Model):
            a: int

        with self.assertRaises(UsageError):
            A(a=1, b=2)  # type: ignore

    def test_build(self):
        class PairInt2Char(Model):
            a: int
            b: char

        pi2c = PairInt2Char(a=1, b=char("2"))
        self.assertEqual(pi2c.build(), b"\x01\x00\x00\x002")

    def test_parse(self):
        class Person(Model):
            name: varchar
            age: byte
            uuid: long

        data = b"\x03Bob\x19\xc9}'\x04\x00\x00\x00\x00"
        bob = Person.parse(data)
        self.assertEqual(bob.name, "Bob")
        self.assertEqual(bob.age, 25)
        self.assertEqual(bob.uuid, 69696969)


    def test_recursive_build(self):
        class PairI2S(Model):
            first: int
            second: varchar

        class Value(Model):
            name: varchar
            kvpair: PairI2S

        data = Value(
            name=varchar("Bob"), kvpair=PairI2S(first=1, second=varchar("123"))
        )

        self.assertEqual(data.build(), b"\x03Bob\x01\x00\x00\x00\x03123")

    def test_recursive_parse(self):
        class PairI2S(Model):
            first: int
            second: varchar

        class Value(Model):
            name: varchar
            kvpair: PairI2S

        data = b"\x03Bob\x01\x00\x00\x00\x03123"
        value = Value.parse(data)
        self.assertEqual(value.name, "Bob")
        self.assertEqual(value.kvpair.first, 1)
        self.assertEqual(value.kvpair.second, "123")
