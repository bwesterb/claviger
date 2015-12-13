import demandimport
demandimport.enable()

import multiprocessing.pool
import argparse
import textwrap
import logging
import sys
import os

import claviger.config
import claviger.worker

import six

l = logging.getLogger(__name__)

class Claviger(object):
    """ main object for claviger """
    def run(self, args):
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

        # As check_server is iobound, the threads are better than processes.
        pool = multiprocessing.pool.ThreadPool(processes=8)
        global_changes = False
        for res in pool.imap_unordered(claviger.worker.check_server,
                (claviger.worker.Job(server=self.cfg['servers'][server_name],
                                    keys=self.cfg['keys'],
                                    dry_run=self.args.dry_run)
                             for server_name in self.cfg['servers'])):
            changes = any([res.n_keys_added, res.n_keys_removed])
            global_changes |= changes
            l.debug('        %s: done', res.server_name)
            if not changes:
                continue
            print ("{0}: {1} keys added, {2} removed".format(res.server_name,
                            res.n_keys_added, res.n_keys_removed))
        if not global_changes:
            print('Everything is in order.')
        elif self.args.dry_run:
            print('')
            print("This is a dry run: no changes have been made.")
            print("Rerun with `-f' to apply changes.")


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
        parser.add_argument('--apply-changes', '-f', action='store_false',
                            dest='dry_run',
                    help='Apply changes')
        self.args = parser.parse_args()




def entrypoint():
    """ entry-point of claviger """
    return Claviger().run(sys.argv[1:])

if __name__ == '__main__':
    entrypoint()
