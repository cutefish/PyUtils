import re

CONFIG_DIR = 'config'
CONFIG_COUNT_FILE = '__count__'
DATA_DIR = 'data'
RESULT_DIR = 'result'
KEY_NAME_REGEX = re.compile('^[a-zA-Z0-9.]+$')
EXPAND_NAME_REGEX = re.compile('@[a-zA-Z0-9.]+')
EXP_POINT_COMMAND_KEY = 'experiment.point.command'
EXP_POINT_ID_KEY = 'experiment.point.id'
EXP_POINT_CONFIG_HEADER = '##### EXPERIMENT POINT #####'
EXP_POINT_CONFIG_END = '##### END #####'
EXP_POINT_ID_ENV_KEY = "PYUTILS_EXP_POINT_ID"
EXP_POINT_OUT_ENV_KEY = "PYUTILS_EXP_POINT_OUT_DIR"

class Point(object):
    def __init__(self, _dict={}):
        self._dict = {}
        self._dict.update(_dict)

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, val):
        self._dict[key] = val

    def __contains__(self, key):
        return self._dict.__contains__(key)

    def update(self, other):
        self._dict.update(other)

    def write(self, fh):
        fh.write('%s = %s\n' %(EXP_POINT_COMMAND_KEY, self._dict[EXP_POINT_COMMAND_KEY]))
        fh.write('%s = %s\n' %(EXP_POINT_ID_KEY, self._dict[EXP_POINT_ID_KEY]))
        for key, value in self._dict.iteritems():
            if key not in [EXP_POINT_COMMAND_KEY, EXP_POINT_ID_KEY]:
                fh.write('%s = %s\n' %(key, value))

    def __str__(self):
        return str(self._dict)


