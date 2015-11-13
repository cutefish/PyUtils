import logging
import logging.config
import sys

from helper import ExecConfHelper
from execution import Execution


def main():
    logging_config()
    src = sys.argv[1]
    cfg_file = '{0}/config.xml'.format(src)
    execution = Execution()
    helper = ExecConfHelper()
    helper.build(execution, cfg_file)
    execution.run()

def logging_config():
    cfg_dict = dict(
        version = 1,
        formatters = {
            'exec_fmt' : { 'format' : '%(message)s' },
            'task_fmt' : { 'format' :
                          '\t[%(log_prefix)s]: %(message)s' },
        },
        handlers = {
            'exec_handler' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'exec_fmt',
                'level' : logging.INFO,
            },
            'task_handler' : {
                'class' : 'logging.StreamHandler',
                'formatter' : 'task_fmt',
                'level' : logging.INFO,
            }
        },
        loggers = {
            'exec' : {
                'handlers' : ['exec_handler'],
                'level' : logging.INFO,
            },
            'task' : {
                'handlers' : ['task_handler'],
                'level' : logging.INFO,
            }
        }
    )
    logging.config.dictConfig(cfg_dict)



if __name__ == '__main__':
    main()
