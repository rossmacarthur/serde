serde
-----

A framework for serializing and deserializing Python objects.

Getting started
---------------

Install this package with

.. code:: bash

    pip install serde


Usage
-----

You can use it like this

.. code:: python

    from serde import Array, Integer, Model, String

    class Address(Model):
        email = String()

    class User(Model):
        name = String()
        age = Integer(optional=True)
        addresses = Array(Address, optional=True)

    # Serialization
    user = User('John Smith', age=53, addresses=[Address('john@smith.com')])
    assert user.to_dict() == {'name': 'John Smith',
                              'age': 53,
                              'addresses': [{'email': 'john@smith.com'}]}

    # Deserialization
    user = User.from_dict({'name': 'John Smith',
                           'age': 53,
                           'addresses': [{'email': 'john@smith.com'}]})
    assert user.name == 'John Smith'
    assert user.age == 53
    assert user.addresses == [Address('john@smith.com')]


License
-------

This project is licensed under the MIT License. See the `LICENSE`_ file.

.. _LICENSE: LICENSE
