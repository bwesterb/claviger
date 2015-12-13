claviger
********

``claviger`` manages the SSH ``authorized_keys`` files for you.

Usage
=====

Tell ``claviger`` which keys you want to put on which server
by creating a ``~/.claviger``-file.  An example::

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
