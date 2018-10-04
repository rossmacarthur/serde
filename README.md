# serde

A framework for *ser*ializing and *de*serializing Python objects.

## Getting started

Install this package with

```bash
pip install serde
```

## Usage

You can use it like this

```python
from serde import Array, Integer, Model, String

class Address(Model):
    email = String()

class User(Model):
    name = String(rename='username')
    age = Integer(optional=True)
    addresses = Array(Address, optional=True)

# Serialization
user = User('John Smith', age=53, addresses=[Address('john@smith.com')])
assert user.to_dict() == {'username': 'John Smith',
                          'age': 53,
                          'addresses': [{'email': 'john@smith.com'}]}

# Deserialization
user = User.from_dict({'username': 'John Smith',
                       'age': 53,
                       'addresses': [{'email': 'john@smith.com'}]})
assert user.name == 'John Smith'
assert user.age == 53
assert user.addresses == [Address('john@smith.com')]
```

## License

This project is licensed under the MIT License. See the [LICENSE] file.

[LICENSE]: LICENSE
