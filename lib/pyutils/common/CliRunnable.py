"""
CliRunnable

Every object/module runnable from command line should define a class that
inherits from this class. This class defines basic interface to run the main
entry of a module.
"""

import sys

class CliRunnable:
    def getAvailableCommand():
        """Return the availabe command dictionary.

        Subclass object should override this method.
        """
        return {}

    def printUsage():
        print getAvailableCommand();

    def run(argv):
        if len(argv == 0):
            printUsage()
            sys.exit(-1)
        func = getattr(self, argv[0])
        func(argv[1:])


