"""
Clirunnable

Every object/module runnable from command line should define a class that
inherits from this class. This class defines basic interface to run the main
entry of a module.
"""

import sys

class CliRunnable:

    def __init__(self):
        """Initialize an availabe command dictionary.

        Subclass object should add their own availableCommand attr.
        """
        self.availableCommand = {
        }


    def getAvailableCommand(self):
        return '\n'.join(
            "  " + key.ljust(20) + ": " + value
            for key, value in sorted(self.availableCommand.iteritems()))

    def printUsage(self):
        print "Available comand:\n" + self.getAvailableCommand();

    def run(self, argv):
        if len(argv) == 0:
            self.printUsage()
            sys.exit(-1)
        func = getattr(self, argv[0])
        func(argv[1:])


