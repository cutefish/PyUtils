import sys

from helper import ExecConfHelper
from execution import Execution


def main():
    src = sys.argv[1]
    cfg_file = '{0}/config.xml'.format(src)
    execution = Execution()
    helper = ExecConfHelper()
    helper.build(execution, cfg_file)
    for task in execution.tasks:
        print task



if __name__ == '__main__':
    main()
