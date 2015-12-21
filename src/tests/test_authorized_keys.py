import unittest
import textwrap

import six

import claviger.authorized_keys

SSHD_MAN_PAGE_EXAMPLE = six.b(textwrap.dedent("""
    # Comments allowed at start of line 
    ssh-rsa AAAAB3NzaC1yc2EAAAA= user@example.net 
    from="*.sales.example.net,!pc.sales.example.net" ssh-rsa AAAAB3NzaC1yc2EAAAA= john@example.net 
    command="dump /home",no-pty,no-port-forwarding ssh-dss AAAAB3NzaC1kc3MAAA== example.net 
    permitopen="192.0.2.1:80",permitopen="192.0.2.2:25" ssh-dss AAAAB3NzaC1kc3MAAA== 
    tunnel="0",command="sh /etc/netstart tun0" ssh-rsa AAAAB3NzaC1yc2EAAAA= jane@example.net 
    restrict,command="uptime" ssh-rsa AAAAB3NzaC1yc2EAAAA= user@example.net 
    restrict,pty,command="nethack" ssh-rsa AAAAB3NzaC1yc2EAAAA= user@example.net
    """))

GRAWITY_EXAMPLE = six.b('ssh-foo="echo \\"Here\'s ssh-rsa for you\\"" '+
                      'future-algo AAAAC2Z1dHVyZS1hbGdv X y z.')

class TestAuthorizedKeys(unittest.TestCase):
    def test_man_page_examples(self):
        f = six.BytesIO(SSHD_MAN_PAGE_EXAMPLE)
        ak = claviger.authorized_keys.parse(f, False)
        self.assertTrue(ak.contains(b'AAAAB3NzaC1yc2EAAAA='))
        self.assertTrue(ak.contains(b'AAAAB3NzaC1kc3MAAA=='))
        self.assertEqual(len(ak.entries), 7)

        g = six.BytesIO()
        ak.store(g)
        self.assertEqual(f.getvalue(), g.getvalue())

    def test_grawity_hard_line(self):
        e = claviger.authorized_keys.Entry.parse(GRAWITY_EXAMPLE)
        self.assertEqual(e.keytype, b'future-algo')

    def test_getters(self):
        f = six.BytesIO(SSHD_MAN_PAGE_EXAMPLE)
        ak = claviger.authorized_keys.parse(f, False)
        self.assertEqual(len(ak.entries), 7)
        self.assertEqual(ak.get(b'doesnotexist'), None)

    def test_remove(self):
        f = six.BytesIO(SSHD_MAN_PAGE_EXAMPLE)
        ak = claviger.authorized_keys.parse(f, False)
        self.assertTrue(ak.contains(b'AAAAB3NzaC1yc2EAAAA='))
        ak.remove(b'AAAAB3NzaC1yc2EAAAA=')
        self.assertFalse(ak.contains(b'AAAAB3NzaC1yc2EAAAA='))
        self.assertTrue(ak.contains(b'AAAAB3NzaC1kc3MAAA=='))
        ak.removeAllKeys()
        self.assertEqual(len(ak.entries), 0)

if __name__ == '__main__':
    unittest.main()
