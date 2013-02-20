"""
expr.txtproc

A text processing util. 

This util implements a form of the MapReduce model where each split is strictly
a text file.

"""
import time

import pyutils.common.fileutils as fil
import pyutils.common.filter as fil
import pyutils.common.reflectutils as ru
import pyutils.common.parser as ps

MODULE_FILE_KEY = "txtproc.module.filename"
INPUT_CLASS_KEY = "txtproc.input.class"
MAPPER_CLASS_KEY = "txtproc.mapper"
REDUCER_CLASS_KEY = "txtproc.reducer"
OUTPUT_CLASS_KEY = "txtproc.output.class"
KEY_CMP_CLASS_KEY = "txtproc.key.cmp.class"
VAL_CMP_CLASS_KEY = "txtproc.val.cmp.class"
OUTPUT_TOKEN_SEPERATOR_KEY = "txtproc.token.seperator"
OUTPUT_LINE_SEPERATOR_KEY = "txtproc.line.seperator"

DEFAULT_INPUT_CLASS = LocalFileFetcher
DEFAULT_MAPPER_CLASS = KeyValueEmitter
DEFAULT_REDUCER_CLASS = IdentityReducer
DEFAULT_OUTPUT_CLASS = KeyValueFileWriter
DEFAULT_OUTPUT_TOKEN_SEPERATOR = " "
DEFAULT_OUTPUT_LINE_SEPERATOR = '\n'

class TxtProc:
    """
    Process a set of text files.

    The processing procedure conforms to a MapReduce programming model. The
    granularity of mapper is a file. Files are fed to mappers, which
    accordingly generates key/value pairs. The key/value pair stream then flows
    to reducer and eventually is written to one file.

    """
    def __init__(self, conf):
        if conf == None:
            raise ValueError("Configuration not specified")
        #get the module
        modFileName = fu.normalizeName(conf.get(MODULE_FILE_KEY))
        modName = modFileName.split('/')[-1].split('.')[0]
        module = ru.loadFileModule(modName, modFileName)
        #input class
        self.inputs = ru.newInstance(
            module, conf.get(INPUT_CLASS_KEY), conf, DEFAULT_OUTPUT_CLASS)
        #mapper
        self.mapper = ru.newInstance(
            module, conf.get(MAPPER_CLASS_KEY), conf, DEFAULT_MAPPER_CLASS)
        #reducer
        self.mapper = ru.newInstance(
            module, conf.get(REDUCER_CLASS_KEY), conf, DEFAULT_REDUCER_CLASS)
        #output class
        self.outputs = ru.newInstance(
            module, conf.get(OUTPUT_CLASS_KEY), conf, DEFAULT_OUTPUT_CLASS)
        #collector
        self.collector = Collector()
        #comparators
        self.keyCmp = ru.newInstance(
            module, conf.get(KEY_CMP_CLASS_KEY), conf, None)
        self.valCmp = ru.newInstance(
            module, conf.get(VAL_CMP_CLASS_KEY), conf, None)

    def run(self):
        #the map stage
        while self.inputs.hasNext():
            self.mapper.run(self.inputs.next(), self.collector)
        self.collector.sort(self.keyCmp, self.valCmp)
        #reduce stage
        for key, values in self.collector.items():
            key, value = self.reducer.run(key, values)
            self.outputs.write(key, value)

class InputFetcher():
    def hasNext(self):
        pass

    def next():
        pass

class Mapper():
    def run(self, fd, collector):
        pass

class Reducer():
    def run(self, key, values):
        pass

class OutputWriter():
    def write(key, value):
        pass

class Collector():
    """
    Intermediate collector.

    Collector collects mapper emitted key/value pairs, sort value inside key
    and sort key and provide the stream to reducer. 
    """
    def __init__(self, conf):
        self._dict = {}
        self.items = []

    def write(self, key, value):
        if not self._dict.has_key(key):
            self._dict[key] = []
        self._dict[key].append(value)

    def sort(self, keyCmp, valueCmp):
        for key in sorted(self._dict.iterkeys(), 
                          key=self.cmp_to_key(keyCmp)):
            values = sorted(self._dict[key],
                            key=self.cmp_to_key(valCmp))
            self.items.append((key, values))

    def cmp_to_key(mycmp):
        """Convert a cmp= function into a key= function."""
        class K(object):
            def __init__(self, obj, *args):
                self.obj = obj

            def __lt__(self, other):
                return mycmp(self.obj, other.obj) < 0

            def __gt__(self, other):
                return mycmp(self.obj, other.obj) > 0

            def __eq__(self, other):
                return mycmp(self.obj, other.obj) == 0

            def __le__(self, other):
                return mycmp(self.obj, other.obj) <= 0  

            def __ge__(self, other):
                return mycmp(self.obj, other.obj) >= 0

            def __ne__(self, other):
                return mycmp(self.obj, other.obj) != 0

        return K

class LocalFileFetcher(InputFetcher):
    """ Fetches file one by one. """
    INPUT_DIR_KEY = "input.local.dir"
    INPUT_FILTER_KEY = "input.filter"

    DEFAULT_FILTER_CLASS = fil.RegexFilter
    def __init__(self, conf):
        self.flist = []
        rootdir = fu.normalizeName(conf.get(INPUT_DIR_KEY))
        if rootdir == None:
            raise ValueError("input.local.dir not specified.")
        modFileName = fu.normalizeName(conf.get(MODULE_FILE_KEY))
        modName = modFileName.split('/')[-1].split('.')[0]
        module = ru.loadFileModule(modName, modFileName)
        fileFilter = ru.newInstance(
            module, conf.get(INPUT_FILTER_KEY), conf, DEFAULT_FILTER_CLASS)
        for f, s in fu.iterFiles(self.rootdir):
            if fileFilter != None:
                if (not fileFilter.accept(f)):
                    continue
            self.flist.append(f)

    def hasNext(self):
        return len(self.flist) != 0

    def next(self):
        return open(self.flist.pop(), 'r');

class KeyValueEmitter(Mapper):
    """
    Emit key/value pairs for each line using KeyValParser.

    Multiple patterns are seperated in the form 
    "pattern0", "pattern1", "pattern2"
    """
    KEYVALUE_PARSE_PATTERN_KEY = "keyvalue.parse.patterns"
    def __init__(self, conf):
        self.parsers = []
        patterns = conf.get("KEYVALUE_PARSE_PATTERN_KEY")
        if patterns == None:
            raise ValueError("key value pattern not set")
        for pattern in patterns.split('"'):
            if pattern.startswith(','):
                continue
            self.parsers.append(ps.KeyValParser(pattern))

    def run(self, fd, collector):
        for line in fd:
            for parser in self.parsers:
                key, val = parser.parse(line)
                collector.write(key, val)
        fd.close()

class IdentityReducer(Reducer):
    """Combine all the values to a space separated string."""
    def __init__(self, conf):
        pass

    def run(self, key, values):
        value = ' '.join([str(v) for v in values])
        return key, value

class KeyValueFileWriter(OutputWriter):
    """Write output to a file."""
    OUTPUT_FILENAME_KEY = "keyvalue.file.writer.filename"
    DEFAULT_FILENAME = "./out_%s" %(int(time.time()))
    def __init__(self, conf):
        filename = fu.normalizeName(
            conf.get(OUTPUT_FILENAME_KEY, DEFAULT_FILENAME))
        self.fd = open(filename, 'w')
        self.tsep = conf.get(
            OUTPUT_TOKEN_SEPERATOR_KEY, DEFAULT_OUTPUT_TOKEN_SEPERATOR)
        self.lsep = conf.get(
            OUTPUT_LINE_SEPERATOR_KEY, DEFAULT_OUTPUT_LINE_SEPERATOR)

    def write(key, value):
        self.fd.write("%s%s%s%s" %(key, self.tsep, value, self.lsep))

    def __del__(self):
        self.fd.close()


class SysStdoutWriter(OutputWriter):
    def __init__(self, conf):
        self.tsep = conf.get(
            OUTPUT_TOKEN_SEPERATOR_KEY, DEFAULT_OUTPUT_TOKEN_SEPERATOR)
        self.lsep = conf.get(
            OUTPUT_LINE_SEPERATOR_KEY, DEFAULT_OUTPUT_LINE_SEPERATOR)

    def write(key, value):
        print "%s%s%s%s" %(key, self.tsep, value, self.lsep)

