import six
import difflib
import collections

import claviger.sftp
import claviger.authorized_keys

Job = collections.namedtuple('Job',
                ('server', 'keys', 'dry_run'))
JobResult = collections.namedtuple('JobResult',
                ('server_name', 'n_keys_added', 'n_keys_removed'))

def check_server(job):
    sftp = claviger.sftp.SFTP()
    n_keys_removed = 0
    n_keys_added = 0
    server = job.server
    conn = sftp.connect(server['hostname'], server['port'],
                                server['ssh_user'])
    original_raw_ak = conn.get(server['user'])
    ak = claviger.authorized_keys.parse(original_raw_ak)
    for key_name in server['present']:
        key = job.keys[key_name]
        # TODO better matching
        if ak.contains(key['key']):
            continue
        n_keys_added += 1
        ak.add(key['options'], key['keytype'], key['key'], key['comment'])
    raw_ak = six.binary_type(ak)
    if job.dry_run:
        print(''.join(difflib.unified_diff(original_raw_ak.splitlines(True),
                        raw_ak.splitlines(True), server['name'])))
    if not job.dry_run and n_keys_added or n_keys_removed:
        conn.put(server['user'], raw_ak)
    return JobResult(server_name=server['name'],
                     n_keys_added=n_keys_added,
                     n_keys_removed=n_keys_removed)
