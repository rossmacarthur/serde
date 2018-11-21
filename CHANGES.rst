Changelog
=========

Version 0.2.1
-------------

*Unreleased*

- Add IpAddress, Ipv4Address, Ipv6Address, and MacAddress Fields. (`#3`_,
  `#30`_)
- Add DateTime, Date, and Time Fields. (`#2`_, `#29`_)

.. _#30: https://github.com/rossmacarthur/serde/pull/30
.. _#29: https://github.com/rossmacarthur/serde/pull/29

.. _#3: https://github.com/rossmacarthur/serde/issues/3
.. _#2: https://github.com/rossmacarthur/serde/issues/2

Version 0.2.0
-------------

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

Version 0.1.2
-------------

*Released on October 28th, 2018*

- Add support for ignoring unknown dictionary keys (`#1`_)

.. _#1: https://github.com/rossmacarthur/serde/pull/1

Version 0.1.1
-------------

*Released on October 27th, 2018*

- Initial release
