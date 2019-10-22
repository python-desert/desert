=====
Usage
=====

To use desert in a project::

        from dataclasses import dataclass
        # from attr import dataclass
        from typing import List

	import desert


        @dataclass
        class Person:
            name: str
            age: int

        @dataclass
        class Car:
            passengers: List[Person]

        # Load some simple data types.
        data = {'passengers': [{'name': 'Alice': 'age': 21}, {'name': 'Bob', 'age': 22}]}


        # Create a schema for the Car object.
        schema = desert.schema(Car)

        # Load the data.
        car = schema.load(car)
        assert car == Car(passengers=[Person(name='Alice', age=21), Person(name='Bob', age=22)])
