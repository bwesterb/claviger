""" Contains the code to check the authorized_keys file on a server.
    
    We run several checks in parallel using the multiprocessing module.
    To avoid serialization (and other) issues, we separate the worker
    environment in this module  with the rest of the program. """

import sys
import difflib
import traceback
import collections

import six

import claviger.sftp
import claviger.authorized_keys

# arguments send by the main process
Job = collections.namedtuple('Job',
                ('server', 'keys', 'dry_run', 'no_diff'))

# this is what we return
JobReturn = collections.namedtuple('JobReturn',
                ('server_name', 'ok', 'result'))
# if everything is ok, the result field is of the following type ...
JobResult = collections.namedtuple('JobResult',
                ('n_keys_added', 'n_keys_removed', 'n_keys_ignored'))
# ... otherwise it is an exception

def check_server(job):
    try:
        sftp = claviger.sftp.SFTP()
        n_keys_removed = 0
        n_keys_added = 0
        n_keys_ignored = 0
        server = job.server
        conn = sftp.connect(server['hostname'], server['port'],
                                    server['ssh_user'])

        # First pull the current authorized_keys
        original_raw_ak = conn.get(server['user'])
        ak = claviger.authorized_keys.parse(original_raw_ak)

        # Check which keys to add
        for key_name in server['present']:
            key = job.keys[key_name]
            # TODO update comment/options
            if ak.contains(key['key']):
                continue
            n_keys_added += 1
            ak.add(key['options'], key['keytype'], key['key'], key['comment'])

        # Check which keys to remove
        if server['keepOtherKeys']:
            for key_name in server['absent']:
                ak.remove(job.keys[key_name]['key'])
                n_keys_removed += 1
        allowed = {job.keys[key_name]['key']
                        for key_name in server['present']}
        for entry in ak.entries:
            if entry.key in allowed:
                continue
            if not server['keepOtherKeys']:
                ak.remove(entry.key)
                n_keys_removed += 1
            else:
                n_keys_ignored += 1

        # Did things change?
        raw_ak = six.binary_type(ak)
        if n_keys_added or n_keys_removed:
            if job.dry_run:
                if not job.no_diff:
                    print(''.join(difflib.unified_diff(
                                    original_raw_ak.splitlines(True),
                                    raw_ak.splitlines(True), server['name'])))
            else:
                conn.put(server['user'], raw_ak)

        return JobReturn(server_name=server['name'], ok=True,
                    result=JobResult(n_keys_added=n_keys_added,
                                     n_keys_removed=n_keys_removed,
                                     n_keys_ignored=n_keys_ignored))
    except claviger.sftp.SFTPError as e:
        return JobReturn(server_name=server['name'], ok=False, result=e)
    except Exception as e:
        # multiprocessing does not pass the stacktrace to the parent process.
        #   ( see http://stackoverflow.com/questions/6126007 )
        # Thus we force the stacktrace in the message.
        raise Exception(''.join(traceback.format_exception(*sys.exc_info())))
