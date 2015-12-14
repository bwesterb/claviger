import demandimport
demandimport.enable()

import multiprocessing.dummy
import itertools
import traceback
import argparse
import textwrap
import logging
import sys
import os

import claviger.config
import claviger.worker
import claviger.sftp


import six

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
        printed_header = False
        errors_occured = False
        for ret in the_map(claviger.worker.check_server,
                (claviger.worker.Job(server=self.cfg['servers'][server_name],
                                    keys=self.cfg['keys'],
                                    dry_run=self.args.dry_run,
                                    no_diff=self.args.no_diff)
                             for server_name in self.cfg['servers'])):
            if not ret.ok:
                errors_occured = True
                if isinstance(ret.result,
                        claviger.sftp.HostKeyVerificationFailed):
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

    def show_configuration_instructions(self):
        print(textwrap.dedent("""
                The configuration file {configfile} does not exist.

                To get started, ... TODO """).format(
                                    configfile=self.args.configfile))
        return 1

    def parse_commandline_args(self):
        parser = argparse.ArgumentParser(
                        description='Synchronize remote SSH authorized_keys')
        parser.add_argument('-c', '--configfile', metavar='PATH',
                                type=os.path.expanduser, default='~/.claviger',
                                help='Configuration file')
        parser.add_argument('--verbose', '-v', action='count',
                            dest='verbosity',
                    help='Add to increase make claviger chatty')
        parser.add_argument('--parallel-connections', '-p', type=int, default=8,
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

def entrypoint():
    """ entry-point of claviger """
    return Claviger().main(sys.argv[1:])

if __name__ == '__main__':
    entrypoint()
