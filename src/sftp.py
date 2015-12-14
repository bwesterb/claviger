import os.path
import logging
import tempfile
import subprocess

l = logging.getLogger(__name__)

class SFTP(object):
    def connect(self, hostname, port,  ssh_user):
        return SFTPSession(hostname, port, ssh_user)


def interpret_scp_error(exitcode, stderr, stdout):
    """ Interpret the output of `scp' and create a suitable exception """
    if 'Host key verification failed' in stderr:
        return HostKeyVerificationFailed()
    msg = 'scp failed: exitcode {0}'.format(exitcode)
    if stderr.strip():
        msg += '; stderr {0}'.format(repr(stderr))
    if stdout.strip():
        msg += '; stdout {0}'.format(repr(stdout))
    return SFTPError(msg)

class SFTPError(Exception):
    pass
class HostKeyVerificationFailed(SFTPError):
    pass

class SFTPSession(object):
    def __init__(self, hostname, port, ssh_user):
        self.hostname = hostname
        self.port = port if port else 22
        self.ssh_user = ssh_user
    def _path_for(self, user):
        # TODO read passwd or use SSH session to find home
        return os.path.join('~' + user, '.ssh', 'authorized_keys')
    def _scp(self, src, trg):
        cmd = ['scp', '-B', '-P', str(self.port), src, trg]
        l.debug('executing %s', cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        stdout_txt, stderr_txt = p.communicate()
        if p.returncode != 0:
            raise interpret_scp_error(p.returncode, stderr_txt, stdout_txt)

    def get(self, user):
        with tempfile.NamedTemporaryFile() as tempf:
            # FIXME escaping
            # TODO check for error
            self._scp('{0}@{1}:{2}'.format(self.ssh_user, self.hostname,
                            self._path_for(user)), tempf.name)
            return tempf.read()
        # TODO create .ssh if it does not exist
        # TODO check permissions
        # TODO backup?
    def put(self, user, authorized_keys):
        with tempfile.NamedTemporaryFile() as tempf:
            tempf.write(authorized_keys)
            tempf.flush()
            self._scp(tempf.name, '{0}@{1}:{2}'.format(self.ssh_user,
                            self.hostname, self._path_for(user)))
