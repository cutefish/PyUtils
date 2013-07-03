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
    def __init__(self, kmap):
        self.kmap = kmap
        self.hashcode = hash(repr(sorted(self.kmap.items())))
        self.vlist = []

    @property
    def keys(self):
        return self.kmap

    @property
    def values(self):
        return self.vlist

    def writeKeys(self, fh):
        fh.write('%s = %s\n' %(EXP_POINT_COMMAND_KEY, self.kmap[EXP_POINT_COMMAND_KEY]))
        fh.write('%s = %s\n' %(EXP_POINT_ID_KEY, self.kmap[EXP_POINT_ID_KEY]))
        for key, value in self.kmap.iteritems():
            if key not in [EXP_POINT_COMMAND_KEY, EXP_POINT_ID_KEY]:
                fh.write('%s = %s\n' %(key, value))

    def __eq__(self, other):
        if self.hashcode != other.hashcode:
            return False
        if self.kmap != other.kmap:
            return False

    def __str__(self):
        return str(self._dict)


