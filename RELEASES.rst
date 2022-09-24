Releases
========

0.9.0
-----

*Released on September 24th, 2022*

- Add `Decimal` field. (`#128`_)
- Drop `isodate` dependency and use standard library. (`de5b598`_)
- Drop Python 2 and Python 3.5 support. (`453b7e6`_)

.. _453b7e6: https://github.com/rossmacarthur/serde/commit/453b7e636e9c39e99de224d9984d5400d4c7f001
.. _de5b598: https://github.com/rossmacarthur/serde/commit/de5b59808c92afe6f2f36c71ec62ce7884dd527a
.. _#128: https://github.com/rossmacarthur/serde/pull/128

0.8.1
-----

*Released on October 8th, 2020*

- Relax ``validators`` dependency requirement. (`c73b194`_)

.. _c73b194: https://github.com/rossmacarthur/serde/commit/c73b194b23dd2ca41437a455921234a39c1870e9

0.8.0
-----

*Released on March 12th, 2020*

- Remove deprecated ``Constant`` field. (`d70b044`_)
- Improve ``ValidationError`` messages for container fields. (`7746732`_)
- Rename ``BaseField`` to ``_Base``. (`c5abc2f`_)
- Add ``frozenset`` to FIELD_CLASS_MAP. (`24d7c0e`_)
- Add ``Flatten`` field. (`9c740a5`_)
- Improve ``Uuid`` field normalization. (`34783b0`_)
- Add ``IpAddress`` field. (`667ca96`_)
- Extended string types now subclass ``Text`` not ``Str``. (`5862375`_)
- Remove `fields.create()` method. (`2a54886`_)
- Completely rework error handling. (`c95b6b3`_)
- Make ``Tag.lookup_tag`` default to module + qualname. (`26963d6`_)

.. _26963d6: https://github.com/rossmacarthur/serde/commit/26963d65b45229db50444665a3160bd0f1358421
.. _c95b6b3: https://github.com/rossmacarthur/serde/commit/c95b6b329125164e3301a7e43292c7a858d5e34f
.. _2a54886: https://github.com/rossmacarthur/serde/commit/2a548865106b1cfc98f5dea8bf00084f62e6334e
.. _5862375: https://github.com/rossmacarthur/serde/commit/5862375ac82a98364d7cf7ef82c6bb668d9abded
.. _667ca96: https://github.com/rossmacarthur/serde/commit/667ca9629028b29a6d420a9ce4eb14460baca448
.. _34783b0: https://github.com/rossmacarthur/serde/commit/34783b03084acffc1fd1cddf4c987d3855d45330
.. _9c740a5: https://github.com/rossmacarthur/serde/commit/9c740a5e9f40b1d913f2d718947f7204e87c6ffa
.. _24d7c0e: https://github.com/rossmacarthur/serde/commit/24d7c0e3320226837586b214ad3dfc0d95852ddb
.. _c5abc2f: https://github.com/rossmacarthur/serde/commit/c5abc2f1d36e9c0857dc1ea65e4536be4c7397ef
.. _7746732: https://github.com/rossmacarthur/serde/commit/7746732d2180d6bd9cbf141475f87409b7977343
.. _d70b044: https://github.com/rossmacarthur/serde/commit/d70b044157e258365868a32daeff4b158b1fbc9d

0.7.3
-----

*Released on January 12th, 2020*

- Fix contained ``Optional`` field (again). (`#120`_)

.. _#120: https://github.com/rossmacarthur/serde/pull/120

0.7.2
-----

*Released on December 2nd, 2019*

- Add ``FrozenSet`` field. (`1d2f0cd`_)
- Add ``Deque`` field. (`ec44671`_)
- Add ``default`` keyword argument to ``Field``. (`#111`_)
- Fix bug in ``Uuid.normalize()``. (`408bc83`_)
- Rename ``Constant`` field to ``Literal``. (`#118`_)

.. _408bc83: https://github.com/rossmacarthur/serde/commit/408bc834ee8c4dbf92438ebcc6e94989927e2d89
.. _ec44671: https://github.com/rossmacarthur/serde/commit/ec44671704529aca505fc10716cde030c9295188
.. _1d2f0cd: https://github.com/rossmacarthur/serde/commit/1d2f0cd09cc49e350ac36ba2697e8023a2f9e47f

.. _#111: https://github.com/rossmacarthur/serde/pull/111
.. _#118: https://github.com/rossmacarthur/serde/pull/118

0.7.1
-----

*Released on September 26th, 2019*

- Add ``Text`` field. (`#110`_, `#116`_)
- Support annotations for specifying fields. (`#99`_, `#115`_)
- Add ``OrderedDict`` field. (`#114`_)
- Add ``Set`` field. (`#113`_)
- Fix contained ``Optional`` field. (`#112`_)

.. _#112: https://github.com/rossmacarthur/serde/pull/112
.. _#113: https://github.com/rossmacarthur/serde/pull/113
.. _#114: https://github.com/rossmacarthur/serde/pull/114
.. _#115: https://github.com/rossmacarthur/serde/pull/115
.. _#116: https://github.com/rossmacarthur/serde/pull/116

.. _#99: https://github.com/rossmacarthur/serde/issues/99
.. _#110: https://github.com/rossmacarthur/serde/issues/110

0.7.0
-----

*Released on September 8th, 2019*

- Embed ``serde-ext`` package code in serde. (`#104`_)
- Rework validators as classes. (`#102`_)
- Documentation overhaul. (`#101`_)
- Rework tags to subclass ``BaseField``. (`#100`_)
- Remove optional extras (`#97`_)

.. _#97: https://github.com/rossmacarthur/serde/pull/97
.. _#100: https://github.com/rossmacarthur/serde/pull/100
.. _#101: https://github.com/rossmacarthur/serde/pull/101
.. _#102: https://github.com/rossmacarthur/serde/pull/102
.. _#104: https://github.com/rossmacarthur/serde/pull/104

0.6.2
-----

*Released on July 20th, 2019*

- Add ``Regex`` field. (`#95`_)
- Drop Python 3.4 support. (`#94`_)

.. _#95: https://github.com/rossmacarthur/serde/pull/95
.. _#94: https://github.com/rossmacarthur/serde/pull/94

0.6.1
-----

*Released on April 4th, 2019*

- Fix some bugs in ``Model`` tagging. (`#92`_)

.. _#92: https://github.com/rossmacarthur/serde/pull/92

0.6.0
-----

*Released on March 30th, 2019*

- Improve base ``Field`` exception messages. (`#86`_)
- Add ``Constant`` field. (`#58`_, `#85`_)
- Model tagging when serializing and deserializing. (`#64`_, `#81`_, `#83`_)
- Streamline sdist. (`#82`_)
- Better error context and handling. (`#38`_, `#80`_)

.. _#86: https://github.com/rossmacarthur/serde/pull/86
.. _#85: https://github.com/rossmacarthur/serde/pull/85
.. _#83: https://github.com/rossmacarthur/serde/pull/83
.. _#82: https://github.com/rossmacarthur/serde/pull/82
.. _#80: https://github.com/rossmacarthur/serde/pull/80

.. _#81: https://github.com/rossmacarthur/serde/issues/81
.. _#64: https://github.com/rossmacarthur/serde/issues/64
.. _#58: https://github.com/rossmacarthur/serde/issues/58
.. _#38: https://github.com/rossmacarthur/serde/issues/38

0.5.2
-----

*Released on February 4th, 2019*

- Add ``Long`` field in Python 2. (`#79`_)
- Fix a bug where validators was a required dependency. (`#78`_)
- Support conversion between Pickle. (`#10`_, `#76`_)

.. _#79: https://github.com/rossmacarthur/serde/pull/79
.. _#78: https://github.com/rossmacarthur/serde/pull/78
.. _#76: https://github.com/rossmacarthur/serde/pull/76

.. _#10: https://github.com/rossmacarthur/serde/issues/10

0.5.1
-----

*Released on January 29th, 2019*

- Reexport `serde-ext`_ fields and validators. (`#75`_)

.. _#75: https://github.com/rossmacarthur/serde/pull/75

0.5.0
-----

*Released on January 29th, 2019*

- Support conversion between CBOR. (`#40`_, `#74`_)
- Remove fields and validators that were moved to `serde-ext`_ package. (`#66`_,
  `#71`_)
- Container fields now properly call inner ``Field`` methods. (`#70`_)
- Add ``equal()`` and ``length()`` validators. (`#67`_, `#69`_)
- Add ``basestring`` and ``unicode`` to built-in ``Field`` map. (`#68`_)

.. _serde-ext: https://github.com/rossmacarthur/serde-ext

.. _#74: https://github.com/rossmacarthur/serde/pull/74
.. _#71: https://github.com/rossmacarthur/serde/pull/71
.. _#70: https://github.com/rossmacarthur/serde/pull/70
.. _#69: https://github.com/rossmacarthur/serde/pull/69
.. _#68: https://github.com/rossmacarthur/serde/pull/68

.. _#67: https://github.com/rossmacarthur/serde/issues/67
.. _#66: https://github.com/rossmacarthur/serde/issues/66
.. _#40: https://github.com/rossmacarthur/serde/issues/40

0.4.1
-----

*Released on January 23rd, 2019*

- Fix a bug where ``Optional`` didn't call the inner ``Field.normalize()``.
  (`#65`_)
- Use 'simplejson' package if available. (`#60`_, `#63`_)
- Fix a bug where ``Choice`` field didn't call ``super().validate()``.
  (`#62`_)

.. _#65: https://github.com/rossmacarthur/serde/pull/65
.. _#63: https://github.com/rossmacarthur/serde/pull/63
.. _#62: https://github.com/rossmacarthur/serde/pull/62

.. _#60: https://github.com/rossmacarthur/serde/issues/60

0.4.0
-----

*Released on January 6th, 2019*

- Fix a bug where dependencies were not pinned correctly. (`#54`_)
- Pluralise module names. (`#52`_)
- Add ``Optional`` field. (`#51`_, `#48`_, `#49`_)

.. _#54: https://github.com/rossmacarthur/serde/pull/54
.. _#52: https://github.com/rossmacarthur/serde/pull/52
.. _#51: https://github.com/rossmacarthur/serde/pull/51

.. _#49: https://github.com/rossmacarthur/serde/issues/49
.. _#48: https://github.com/rossmacarthur/serde/issues/48

0.3.2
-----

*Released on December 19th, 2018*

- Fix a bug where overriding ``Model.__init__()`` method affected
  ``Model.from_dict``. (`#45`_, `#46`_)

.. _#46: https://github.com/rossmacarthur/serde/pull/46

.. _#45: https://github.com/rossmacarthur/serde/issues/45

0.3.1
-----

*Released on December 17th, 2018*

- Fix a bug with the ``Model.__repr__()`` method. (`#44`_)
- Make ``Bytes`` an alias of ``Str`` in Python 2.7. (`#43`_)
- Fix not being able to create attributes, methods, and functions with the same
  name as fields on a ``Model``. (`#41`_, `#42`_)

.. _#44: https://github.com/rossmacarthur/serde/pull/44
.. _#43: https://github.com/rossmacarthur/serde/pull/43
.. _#42: https://github.com/rossmacarthur/serde/pull/42

.. _#41: https://github.com/rossmacarthur/serde/issues/41

0.3.0
-----

*Released on December 9th, 2018*

- Support Python 2.7. (`#35`_)
- Add ``BaseString`` and ``Unicode`` fields. (`#35`_)
- Remove extra validation options from built-in type Fields. (`#34`_)
- Add ``min()`` and ``max()`` validation functions. (`#34`_)
- Add ``inclusive`` option to ``between()`` validator. (`#34`_)
- Add ``args`` option to the ``field.create()`` method. (`#34`_)
- Generate built-in types using the ``field.create()`` method. (`#34`_)
- Add ``Complex`` and ``Bytes`` fields. (`#34`_)
- Do not clutter root namespace with fields. (`#34`_)

.. _#35: https://github.com/rossmacarthur/serde/pull/35
.. _#34: https://github.com/rossmacarthur/serde/pull/34

0.2.1
-----

*Released on November 21th, 2018*

- Fix ``SerdeErrors`` having incorrect context. (`#32`_)
- Add ``IpAddress``, ``Ipv4Address``, ``Ipv6Address``, and ``MacAddress``
  fields. (`#3`_, `#30`_)
- Add ``DateTime``, ``Date``, and ``Time`` fields. (`#2`_, `#29`_)

.. _#32: https://github.com/rossmacarthur/serde/pull/30
.. _#30: https://github.com/rossmacarthur/serde/pull/30
.. _#29: https://github.com/rossmacarthur/serde/pull/29

.. _#3: https://github.com/rossmacarthur/serde/issues/3
.. _#2: https://github.com/rossmacarthur/serde/issues/2

0.2.0
-----

*Released on November 16th, 2018*

- Add validate module with validate functions for use with fields. (`#22`_)
- Support ``Field`` creation from functions. (`#22`_)
- General API improvements. (`#17`_)
- Support conversion between TOML, YAML. (`#7`_, `#8`_, `#16`_)
- Add ``Boolean``, ``Dictionary``, ``Integer``, and ``String`` aliases.
  (`#11`_, `#14`_)
- Add ``serializers`` and ``deserializers`` ``Field`` options for arbitrary
  serializer and deserializer functions. (`#6`_)
- ``Nested`` fields now take the same options as ``to_dict()`` and
  ``from_dict()`` on ``Model`` objects. (`#5`_)

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

- Initial release, fixed.

0.1.0
-----

*Released on October 27th, 2018*

- Initial release, yanked.
