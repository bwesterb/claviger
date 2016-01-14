claviger Changelog
******************

0.1.3 (unreleased)
==================

- Add ``allow``-list to server stanza.

  If ``keepOtherKeys`` is set to false, claviger will remove any keys present
  except for those in the ``present`` and ``allow`` list.
- Add *abstract servers*.  Let every server inherit from the hidden
  abstract server ``$default``.
- Allow

  .. code:: yaml

    servers:
        server1:
        server2:

  which is prettier than

  .. code:: yaml

    servers:
        server1: {}
        server2: {}

- bugfix: actually set server name with ``name`` option.


0.1.2 (2016-01-08)
==================

- Show the correct number of keys actually removed.


0.1.1 (2015-12-21)
==================

- Some cosmetic changes.
- Show example configuration file, if claviger isn't configured yet.
- Python 3 compatibility.

0.1.0 (2015-12-14)
==================

- Initial release.
