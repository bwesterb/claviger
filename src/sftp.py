import os.path
import logging
import tempfile
import subprocess

l = logging.getLogger(__name__)

class SFTP(object):
    def connect(self, hostname, port,  ssh_user):
        return SFTPSession(hostname, port, ssh_user)

class SFTPError(Exception):
    def __init__(self, message, exitcode):
        super(SFTPError, self).__init__(message)
        self.exitcode = exitcode

class SFTPSession(object):
    def __init__(self, hostname, port, ssh_user):
        self.hostname = hostname
        self.port = port if port else 22
        self.ssh_user = ssh_user
    def _path_for(self, user):
        # TODO read passwd or use SSH session to find home
        return os.path.join('~' + user, '.ssh', 'authorized_keys')
    def get(self, user):
        with tempfile.NamedTemporaryFile() as tempf:
            # FIXME escaping
            # TODO check for error
            cmd = ['scp', '-qB', '-P', str(self.port),
                    '{0}@{1}:{2}'.format(self.ssh_user,
                    self.hostname, self._path_for(user)), tempf.name]
            l.debug("get: executing %s", cmd)
            with open(os.devnull, 'w') as fnull:
                ret = subprocess.call(cmd, stdout=fnull, stderr=fnull)
                if ret != 0:
                    raise SFTPError('scp failed with exitcode {0}'.format(ret),
                                            ret) 
            return tempf.read()
        # TODO create .ssh if it does not exist
        # TODO check permissions
        # TODO backup?
    def put(self, user, authorized_keys):
        with tempfile.NamedTemporaryFile() as tempf:
            tempf.write(authorized_keys)
            tempf.flush()
            cmd = ['scp', '-qB', '-P', str(self.port),
                    tempf.name, '{0}@{1}:{2}'.format(self.ssh_user,
                    self.hostname, self._path_for(user))]
            l.debug("get: executing %s", cmd)
            with open(os.devnull, 'w') as fnull:
                ret = subprocess.call(cmd, stdout=fnull, stderr=fnull)
                if ret != 0:
                    raise SFTPError('put scp failed with exitcode {0}'.format(
                                        ret), ret) 
