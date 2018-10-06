# Serde

**Serde** is a general-purpose, extendable framework for *ser*ializing and
*de*serializing Python objects. Objects are defined with a Model schema and can
be converted to and from dictionaries. Input values can be validated with
arbitrary functions.

## Installing

Install this package with

```bash
pip install serde
```

## Usage

First describe your data

```python
class Version(Model):
    major = Integer()
    minor = Integer()
    patch = Integer(optional=True, default=0)

class Package(Model):
    name = String(name='packageName')
    version = ModelField(Version)
```

Easily instantiate and use a model

```python
package = Package('requests', Version(2, 19, 1))

assert package.name == 'requests'
assert package.version.major == 2
assert package.version.minor == 19
assert package.version.patch == 1
```

Serialize the Model as a dictionary

```python
assert package.to_dict() == {
    'packageName': 'requests',
    'version': {
        'major': 2,
        'minor': 19,
        'patch': 1
    }
}
```

Deserialize another Model from a dictionary

```python
package = Package.from_dict({
    'packageName': 'click',
    'version': {
        'major': 7,
        'minor': 0
    }
})

assert package.name == 'click'
assert package.version.major == 7
assert package.version.minor == 0
assert package.version.patch == 0
```

## API Reference

This part of the documentation lists the full API reference of all public
classes and functions.

- [Model](model.rst)
- [Fields](fields.rst)
- [Exceptions](exceptions.rst)
