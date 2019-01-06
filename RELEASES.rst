Releases
========

0.4.0
-----

*Released on January 6th, 2019*

- Fix a bug where dependencies were not pinned correctly. (`#54`_)
- Pluralise module names. (`#52`_)
- Add Optional Field. (`#51`_, `#48`_, `#49`_)

.. _#54: https://github.com/rossmacarthur/serde/pull/54
.. _#52: https://github.com/rossmacarthur/serde/pull/52
.. _#51: https://github.com/rossmacarthur/serde/pull/51

.. _#49: https://github.com/rossmacarthur/serde/issues/49
.. _#48: https://github.com/rossmacarthur/serde/issues/48

0.3.2
-----

*Released on December 19th, 2018*

- Fix a bug where overriding Model `__init__` method affected Model `from_dict`.
  (`#45`_, `#46`_)

.. _#46: https://github.com/rossmacarthur/serde/pull/46

.. _#45: https://github.com/rossmacarthur/serde/issues/45

0.3.1
-----

*Released on December 17th, 2018*

- Fix a bug with the Model `__repr__` method. (`#44`_)
- Make Bytes an alias of Str Field in Python 2.7. (`#43`_)
- Fix not being able to create attributes, methods, and functions with the same
  name as Fields on a Model. (`#41`_, `#42`_)

.. _#44: https://github.com/rossmacarthur/serde/pull/44
.. _#43: https://github.com/rossmacarthur/serde/pull/43
.. _#42: https://github.com/rossmacarthur/serde/pull/42

.. _#41: https://github.com/rossmacarthur/serde/issues/41

0.3.0
-----

*Released on December 9th, 2018*

- Support Python 2.7. (`#35`_)
- Add BaseString and Unicode Fields. (`#35`_)
- Remove extra validation options from built-in type Fields. (`#34`_)
- Add min() and max() validation functions. (`#34`_)
- Add "inclusive" option to between() validator. (`#34`_)
- Add "args" option to the field.create() method. (`#34`_)
- Generate built-in types using the field.create() method. (`#34`_)
- Add Complex and Bytes Fields. (`#34`_)
- Do not clutter root namespace with Fields. (`#34`_)

.. _#35: https://github.com/rossmacarthur/serde/pull/35
.. _#34: https://github.com/rossmacarthur/serde/pull/34

0.2.1
-----

*Released on November 21th, 2018*

- Fix SerdeErrors having incorrect context. (`#32`_)
- Add IpAddress, Ipv4Address, Ipv6Address, and MacAddress Fields. (`#3`_,
  `#30`_)
- Add DateTime, Date, and Time Fields. (`#2`_, `#29`_)

.. _#32: https://github.com/rossmacarthur/serde/pull/30
.. _#30: https://github.com/rossmacarthur/serde/pull/30
.. _#29: https://github.com/rossmacarthur/serde/pull/29

.. _#3: https://github.com/rossmacarthur/serde/issues/3
.. _#2: https://github.com/rossmacarthur/serde/issues/2

0.2.0
-----

*Released on November 16th, 2018*

- Add validate module with validate functions for use with Fields. (`#22`_)
- Support Field creation from functions. (`#22`_)
- General API improvements. (`#17`_)
- Support conversion between TOML, YAML. (`#7`_, `#8`_, `#16`_)
- Add Boolean, Dictionary, Integer, and String Field aliases. (`#11`_, `#14`_)
- Add ``serializers`` and ``deserializers`` Field options for arbitrary
  serializer and deserializer functions. (`#6`_)
- Nested Fields now take the same options as ``to_dict()`` and ``from_dict()``
  on Model objects. (`#5`_)

.. _#22: https://github.com/rossmacarthur/serde/pull/22
.. _#17: https://github.com/rossmacarthur/serde/pull/17
.. _#16: https://github.com/rossmacarthur/serde/pull/16
.. _#14: https://github.com/rossmacarthur/serde/pull/14
.. _#6: https://github.com/rossmacarthur/serde/pull/6
.. _#5: https://github.com/rossmacarthur/serde/pull/5

.. _#11: https://github.com/rossmacarthur/serde/issues/11
.. _#8: https://github.com/rossmacarthur/serde/issues/8
.. _#7: https://github.com/rossmacarthur/serde/issues/7

0.1.2
-----

*Released on October 28th, 2018*

- Add support for ignoring unknown dictionary keys (`#1`_)

.. _#1: https://github.com/rossmacarthur/serde/pull/1

0.1.1
-----

*Released on October 27th, 2018*

- Initial release
