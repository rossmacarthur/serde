Changelog
=========

Version 0.2.0
-------------

*Unreleased*

- Add validate module with validate functions for use with Fields. (`#22`_)
- Support Field creation from functions. (`#22`_)
- General API improvements. (`#17`_)
- Support conversion between TOML, YAML. (`#7`_, `#8`_, `#16`_)
- Add Boolean, Dictionary, Integer, and String Field aliases. (`#11`_, `#14`_)
- Add `serializers` and `deserializers` Field options for arbitrary serializer
  and deserializer functions. (`#6`_)
- Nested Fields now take the same options as `to_dict()` and `from_dict()` on
  Model objects. (`#5`_)

.. _#22: https://github.com/rossmacarthur/serde/pull/22
.. _#16: https://github.com/rossmacarthur/serde/pull/17
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
