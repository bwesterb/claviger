claviger
********

``claviger`` manages the SSH ``authorized_keys`` files for you.

Quick introduction
==================

Tell ``claviger`` which keys you want to put on which server
by creating a ``~/.claviger``-file.  An example

.. code:: yaml

    keys:
        laptop: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINYZEwjtu8w9Hsvx85TlYE95MLV9Whc3N1ajrH7+gu7A
        desktop: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICUef9frJIX7tjvZkYYMtr4IdD/GcKz6/X5qvLxM1Z8O desktop
        work: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICrycv44eyFwWJ7QQsGOnjEiAsFSdxIoAEzBPSO/AQB5 work
    servers:
        myprivateserver.com:
            user: myusername
            present:
                - laptop
                - desktop
        root@myotherserver.com:
            like: myprivateserver.com
            present:
                - work
            keepOtherKeys: false
        workuser@workserver.com:
            present:
                - work
                - desktop
            absent:
                - laptop

Then run ``claviger``.  By default ``claviger`` only tells which changes
it wants to make, but does not make them.  If the changes seem fine,
run ``claviger -f``, which allows ``claviger`` to make changes.

Installation
============

To install ``claviger``, simply run::

   pip install claviger


Claviger config file
====================

A ``.claviger`` is written in YAML_.  It consists of two maps: the ``keys``
map and the ``servers`` map.

.. code:: yaml

    servers:
        server_key:
            # ... (server stanza)
        server_key2:
            # ... (server stanza)
    keys:
        key_name: # ... (ssh public key)
        key_name2: # ... (ssh public key)

As seen in the example at the top, the ``keys`` map has as values SSH
public keys as they would appear in an ``authorized_keys`` file.

The ``servers`` map consists of key-stanza pairs.  Each stanza is a map
of option name/value pairs, like:

.. code:: yaml

    server_key:
        option_name: option_value
        option_name2: option_value
        # ...

See below for the available options in the server-stanza's.

Server key
----------

The key of a server stanza is of the following form::

    [user@]hostname[:port]

Examples of keys are

- ``just-a-hostname.nl``
- ``user@some-server.com``
- ``some-server.nl:1234``
- ``user@and-port.com:22022``

You can also specify ``user``, ``hostname`` and ``port`` explicitly.
See below.

If a server key starts with a dollar sign (for instance ``$work``),
then it is considered ``abstract`` --- see below.

Server stanzas
--------------

A server stanza is a map which may have the following entries.

================== =============================================================
``name``           | The name of the server.
                   | *Default*: stanza key.
``hostname``       | The hostname of the server.
                   | *Default*: derived from stanza key.
``user``           | The user for which to manage the ``authorized_keys`` file
                   | *Default*: ``root`` if not derived from stanza key.
``present``        | A list of key names that must be in the
                     ``authorized_keys`` file.
                   | *Default*: the empty list ``[]``
``absent``         | A list of SSH-keys that should be removed from the
                     ``authorized_keys`` file.
                   | *Default*: the empty list ``[]``
``keepOtherKeys``  | ``true`` or ``false``.  If set to ``false``, ``claviger``
                     will remove all keys not explicitly allowed form the
                     ``authorized_keys`` file.
                   | *Default*: ``true``.
``allow``          | A list of SSH-keys that are also allowed to be in the
                     ``authorized_keys`` file if ``keepOtherKeys`` is set
                     to ``false``.  These keys will not be added, if
                     not present already.
                   | *Default*: the empty list ``[]``
``like``           | Name of another server stanza.  If set, the entries of
                     the other server stanza will be used as default values
                     for this server stanza.
                   | *Default*: ``$default``
``ssh_user``       | The user to use to get and put the
                     ``authorized_keys`` file.
                   | *Default*: the same as ``user``
``port``           | The port to use to connect to the server.
                   | *Default*: 22.
``abstract``       | ``true`` or ``false``. If set to ``true``, ``claviger``
                     will not check this server.  See below.
                   | *Default*: ``false``
================== =============================================================


Abstract servers and ``$default``
---------------------------------

``claviger`` will not check an *abstract* server.  This is useful to cleanly
configure multiple server.

.. code:: yaml

    servers:
        $mine:
            keepOthers: false
            present:
                - my_first_key
                - my_second_key
        $work:
            present:
                - my_work_key
            absent:
                - my_first_key

        my-first-server.tld:
            like: $mine
        my-second-server.tld:
            like: $mine
        alpha.at-work.tld:
            like: $work
        beta.at_work.tld:
            like: $work

By default, server inherits from the hidden ``$default`` abstract server.

.. code:: yaml

    servers:
        $default:
            user: myname
            present:
                - this_key_is_put_everywhere
        host1.tld: # will use myname as user
        host2.tld: # "
        root@host3.tld  # will use root as user
        host4.tld:
            absent:
                - this_key_is_put_everywhere # except here


.. _YAML: http://yaml.org
