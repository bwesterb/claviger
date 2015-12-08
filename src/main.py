import demandimport
demandimport.enable()

import argparse
import textwrap
import sys
import os


class Claviger(object):
    """ main object for claviger """
    def run(self, args):
        self.parse_commandline_args()
        if not os.path.exists(self.args.configfile):
            return self.show_configuration_instructions()

    def show_configuration_instructions(self):
        print(textwrap.dedent("""
                The configuration file {configfile} does not exist.

                To get started, ... TODO """).format(
                                    configfile=self.args.configfile))
        return 1

    def parse_commandline_args(self):
        parser = argparse.ArgumentParser(
                        description='Synchronize remote SSH authorized_keys')
        parser.add_argument('--configfile', metavar='PATH',
                                type=os.path.expanduser, default='~/.claviger',
                                help='Configuration file')
        self.args = parser.parse_args()



def entrypoint():
    """ entry-point of claviger """
    return Claviger().run(sys.argv[1:])

if __name__ == '__main__':
    entrypoint()
