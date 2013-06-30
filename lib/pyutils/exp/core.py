import re

CONFIG_DIR = 'config'
CONFIG_COUNT_FILE = '__count__'
DATA_DIR = 'data'
RESULT_DIR = 'result'
KEY_NAME_REGEX = re.compile('^[a-zA-Z0-9.]+$')
EXPAND_NAME_REGEX = re.compile('\$[a-zA-Z0-9.]+')
EXP_COMMAND_KEY = 'experiment.run.command'
EXP_POINT_ID_KEY = 'experiment.point.id'
EXP_POINT_CONFIG_HEADER = '##### EXPERIMENT POINT #####'
EXP_POINT_CONFIG_END = '##### END #####'

