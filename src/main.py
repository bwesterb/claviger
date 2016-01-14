import demandimport
demandimport.enable()

import multiprocessing.dummy
import itertools
import traceback
import argparse
import textwrap
import os.path
import logging
import sys
import os

import claviger.authorized_keys
import claviger.config
import claviger.worker
import claviger.scp

import six
import yaml

l = logging.getLogger(__name__)

class Claviger(object):
    """ main object for claviger """
    def main(self, args):
        try:
            self.parse_commandline_args()

            extra_logging_config = {}
            if self.args.verbosity >= 2:
                level = logging.DEBUG
                extra_logging_config['format'] = ('%(relativeCreated)d '+
                        '%(levelname)s %(name)s %(message)s')
            elif self.args.verbosity == 1:
                level = logging.INFO
            else:
                level = logging.WARNING
            logging.basicConfig(level=level, **extra_logging_config)

            if not os.path.exists(self.args.configfile):
                return self.show_configuration_instructions()
            self.cfg = claviger.config.load(self.args.configfile)
            self.check_servers()
        except Exception:
            return self.handle_uncaught_exception()

    def check_servers(self):
        if self.args.parallel_connections == 1:
            # If we want one worker, the current thread will do just fine.
            the_map = itertools.imap
        else:
            # As check_server is iobound, threads are better than processes.
            pool = multiprocessing.dummy.Pool(
                            processes=self.args.parallel_connections)
            the_map = pool.imap_unordered

        global_changes = False
        errors_occured = False
        for ret in the_map(claviger.worker.check_server,
                (claviger.worker.Job(server=self.cfg['servers'][server_name],
                                    keys=self.cfg['keys'],
                                    dry_run=self.args.dry_run,
                                    no_diff=self.args.no_diff)
                         for server_name in self.cfg['servers']
                         if not self.cfg['servers'][server_name]['abstract'])):
            if not ret.ok:
                errors_occured = True
                if isinstance(ret.result,
                        claviger.scp.HostKeyVerificationFailed):
                    print("{0:<40} host key verification failed".format(
                                ret.server_name))
                else:
                    print("")
                    print("{0:<40} error".format(ret.server_name))
                    print("   {0}".format(ret.result))
                    print("")
                continue
            res = ret.result
            changes = any([res.n_keys_added, res.n_keys_removed])
            global_changes |= changes
            l.debug('        %s: done', ret.server_name)
            if not changes and not self.args.verbosity:
                continue
            print ("{0:<40} +{1:<2} -{2:<2} ?{3:<2}".format(ret.server_name,
                            res.n_keys_added, res.n_keys_removed,
                            res.n_keys_ignored))
        if not global_changes and not errors_occured:
            print('Everything is in order.')
        elif self.args.dry_run and not errors_occured:
            print('')
            print("This is a dry run: no changes have been made.")
            print("Rerun with `-f' to apply changes.")
        elif errors_occured:
            print('')
            print('Checking some servers failed.  See above.')
            if self.args.dry_run:
                print("This is a dry run: no changes have been made.")

    def find_ssh_pubkeys(self):
        """ Searches for SSH public keys in the user's homedir.

            Return a list of (unique_name, pubkey) pairs. """
        ret = []
        names = set()
        ssh_dir = os.path.expanduser("~/.ssh")
        if not os.path.isdir(ssh_dir):
            return ret
        for fn in os.listdir(ssh_dir):
            if not fn.startswith('id_') or not fn.endswith('.pub'):
                continue
            with open(os.path.join(ssh_dir, fn), 'rb') as f:
                raw_pubkey = f.readline()
                if not raw_pubkey:
                    continue
                raw_pubkey = raw_pubkey[:-1]
            try:
                pubkey = claviger.authorized_keys.Entry.parse(raw_pubkey)
            except claviger.authorized_keys.CouldNotParseLine:
                continue
            name = pubkey.comment if pubkey.comment else 'mykey'
            if name in names:
                i = 2
                while name + str(i) in names:
                    i += 1
                name = name + str(i)
            names.add(name)
            ret.append((name, raw_pubkey))
        return ret

    def show_configuration_instructions(self):
        keys = self.find_ssh_pubkeys()
        if not keys:
            keys = [('exampleKey', 'ssh-rsa AAAAHitsanexamplekey comment')]
        print(textwrap.dedent("""
                The configuration file {configfile} does not exist.

                An example config file is:

                    keys: """).format(configfile=self.args.configfile))
        for name, key in keys:
            print("        {0}: {1}".format(yaml_str(name), yaml_str(key)))
        print(textwrap.dedent("""
                    servers:
                        user@example.com:
                            present:""").replace('\n','\n    ')[1:])
        for name, keys in keys:
            print("               - {0}".format(yaml_str(name)))
        return 1

    def parse_commandline_args(self):
        parser = argparse.ArgumentParser(
                        description='Synchronize remote SSH authorized_keys')
        parser.add_argument('-c', '--configfile', metavar='PATH',
                                type=os.path.expanduser, default='~/.claviger',
                                help='Configuration file')
        parser.add_argument('--verbose', '-v', action='count',
                            dest='verbosity', default=0,
                    help='Add to increase make claviger chatty')
        parser.add_argument('--parallel-connections', '-p', metavar='N',
                                type=int, default=8,
                    help='Number of parallel connections')
        parser.add_argument('--apply-changes', '-f', action='store_false',
                            dest='dry_run',
                    help='Apply changes')
        parser.add_argument('--no-diff', '-s', action='store_true',
                    help='Do not show a diff during the dry run')
        self.args = parser.parse_args()

    def handle_uncaught_exception(self):
        sys.stderr.write('\n')
        sys.stderr.write('An unexpected exception occured:\n')
        sys.stderr.write('\n    ')
        sys.stderr.write(traceback.format_exc().replace('\n', '\n    '))
        sys.stderr.write('\n')
        sys.stderr.write('Please report this error:\n')
        sys.stderr.write('\n')
        sys.stderr.write('  https://github.com/bwesterb/claviger/issues\n')
        sys.stderr.write('\n')
        sys.stderr.flush()
        return 2

def yaml_str(s):
    """ Escapes the string for inclusion in YAML. """
    if not isinstance(s, six.string_types):
        s = s.decode('utf-8')
    ret = yaml.dump(s)
    if ret.endswith('\n'):
        ret = ret[:-1]
    if ret.endswith('\n...'):
        ret = ret[:-4]
    return ret

def entrypoint():
    """ entry-point of claviger """
    return Claviger().main(sys.argv[1:])

if __name__ == '__main__':
    entrypoint()
