"""
expr.txtproc

A text processing util. 

This util implements a form of the MapReduce model where each split is strictly
a text file.

"""
import sys
import time

import pyutils.common.clirunnable as clir
import pyutils.common.fileutils as fu
import pyutils.common.filter as fil
import pyutils.common.importutils as iu
import pyutils.common.parser as ps


###########################################################
# Settings
###########################################################

EXTRA_PATHS_KEY = "txtproc.extra.paths"
INPUT_CLASS_KEY = "txtproc.input.class"
MAPPER_CLASS_KEY = "txtproc.mapper.class"
REDUCER_CLASS_KEY = "txtproc.reducer.class"
OUTPUT_CLASS_KEY = "txtproc.output.class"
KEY_CMP_CLASS_KEY = "txtproc.key.cmp.class"
VAL_CMP_CLASS_KEY = "txtproc.val.cmp.class"
OUTPUT_TOKEN_SEPERATOR_KEY = "txtproc.token.seperator"
OUTPUT_LINE_SEPERATOR_KEY = "txtproc.line.seperator"

INPUT_DIR_KEY = "txtproc.input.local.dir"
INPUT_FILTER_KEY = "txtproc.input.filter"
INPUT_FILTER_PATTERN_KEY = "txtproc.input.filter.pattern"

###########################################################
# Specific Implements
###########################################################

class InputFetcher():
    def hasNext(self):
        pass

    def next(self):
        pass

    def __str__(self):
        return 'InputFetcher: ' + self.__class__

class Mapper():
    def run(self, fd, collector):
        pass

    def __str__(self):
        return 'Mapper: ' + self.__class__

class Reducer():
    def run(self, key, values):
        pass

    def __str__(self):
        return 'Reducer: ' + self.__class__

class OutputWriter():
    def write(key, value):
        pass

    def __str__(self):
        return 'OutputWriter: ' + self.__class__

class Collector():
    """
    Intermediate collector.

    Collector collects mapper emitted key/value pairs, sort value inside key
    and sort key and provide the stream to reducer. 
    """
    def __init__(self, conf):
        self._dict = {}
        self._items = []

    def items(self):
        return self._items

    def write(self, key, value):
        if not self._dict.has_key(key):
            self._dict[key] = []
        self._dict[key].append(value)

    def sort(self, keyCmp, valCmp):
        if keyCmp != None:
            keyFunc = self.cmp_to_key(keyCmp)
        else:
            keyFunc = None
        if valCmp != None:
            valFunc = self.cmp_to_key(valCmp)
        else:
            valFunc = None
        for key in sorted(self._dict.iterkeys(), 
                          key=keyFunc):
            values = sorted(self._dict[key],
                            key=valFunc)
            self._items.append((key, values))

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

    def __init__(self, conf):
        self.flist = []
        rootdir = fu.normalizeName(conf.get(INPUT_DIR_KEY))
        if rootdir == None:
            raise ValueError("input.local.dir not specified.")
        extraPaths = conf.getStrings(EXTRA_PATHS_KEY)
        filterCls = conf.getClass(INPUT_FILTER_KEY, DEFAULT_FILTER_CLASS,
                                  extraPaths)
        pattern = conf.get(INPUT_FILTER_PATTERN_KEY)
        fileFilter = filterCls(pattern)
        for f, s in fu.iterFiles(rootdir):
            if fileFilter != None:
                if (not fileFilter.accept(f)):
                    continue
            self.flist.append(f)

    def hasNext(self):
        return len(self.flist) != 0

    def next(self):
        return open(self.flist.pop(), 'r');

    def __str__(self):
        return str(self.flist)

class KeyValueEmitter(Mapper):
    """
    Emit key/value pairs for each line using KeyValParser.

    Multiple patterns are seperated in the form 
    "pattern0", "pattern1", "pattern2"
    """
    KEYVALUE_PARSE_PATTERN_KEY = "keyvalue.parse.patterns"
    def __init__(self, conf):
        self.parsers = []
        patterns = conf.get(self.KEYVALUE_PARSE_PATTERN_KEY)
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

    def __str__(self):
        ret = ""
        ret += "KeyValueEmitter: parsers: " 
        ret += "["
        for p in self.parsers:
            ret += "( " + str(p) + "), "
        ret += "]"
        return ret

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

    def write(self, key, value):
        self.fd.write("%s%s%s%s" %(key, self.tsep, value, self.lsep))

    def __del__(self):
        self.fd.close()

    def __str__(self):
        return "KeyValueFileWriter: " + \
                "out file= " + self.fd.name

class SysStdoutWriter(OutputWriter):
    def __init__(self, conf):
        self.tsep = conf.get(
            OUTPUT_TOKEN_SEPERATOR_KEY, DEFAULT_OUTPUT_TOKEN_SEPERATOR)
        self.lsep = conf.get(
            OUTPUT_LINE_SEPERATOR_KEY, DEFAULT_OUTPUT_LINE_SEPERATOR)

    def write(self, key, value):
        print "%s%s%s%s" %(key, self.tsep, value, self.lsep)

    def __str__(self):
        return "SysStdoutWriter."

###########################################################
# TxtProc
###########################################################

DEFAULT_INPUT_CLASS = LocalFileFetcher
DEFAULT_MAPPER_CLASS = KeyValueEmitter
DEFAULT_REDUCER_CLASS = IdentityReducer
DEFAULT_OUTPUT_CLASS = KeyValueFileWriter
DEFAULT_OUTPUT_TOKEN_SEPERATOR = " "
DEFAULT_OUTPUT_LINE_SEPERATOR = '\n'

DEFAULT_FILTER_CLASS = fil.RegexFilter

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
        extraPaths = conf.getStrings(EXTRA_PATHS_KEY)
        #input class
        inputsCls = conf.getClass(INPUT_CLASS_KEY, DEFAULT_INPUT_CLASS,
                                  extraPaths)
        self.inputs = inputsCls(conf)
        #mapper
        mapperCls = conf.getClass(MAPPER_CLASS_KEY, DEFAULT_MAPPER_CLASS,
                                  extraPaths)
        self.mapper = mapperCls(conf)
        #reducer
        reducerCls = conf.getClass(REDUCER_CLASS_KEY, DEFAULT_REDUCER_CLASS, 
                                   extraPaths)
        self.reducer = reducerCls(conf)
        #output class
        outputCls = conf.getClass(OUTPUT_CLASS_KEY, DEFAULT_OUTPUT_CLASS, 
                                  extraPaths)
        self.outputs = outputCls(conf)
        #collector
        self.collector = Collector(conf)
        #comparators
        self.keyCmp = conf.getClass(KEY_CMP_CLASS_KEY, path=extraPaths)
        self.valCmp = conf.getClass(VAL_CMP_CLASS_KEY, path=extraPaths)

    def run(self):
        #the map stage
        while self.inputs.hasNext():
            self.mapper.run(self.inputs.next(), self.collector)
        self.collector.sort(self.keyCmp, self.valCmp)
        #reduce stage
        for key, values in self.collector.items():
            key, value = self.reducer.run(key, values)
            self.outputs.write(key, value)

    def __str__(self):
        ret = ""
        ret += "TxtProc: \n"
        ret += "inputs: " + str(self.inputs) + "\n"
        ret += "mapper: " + str(self.mapper) + "\n"
        ret += "reducer: " + str(self.reducer) + "\n"
        ret += "outputs: " + str(self.outputs) + "\n"
        return ret

class TxtProcRunnable(clir.CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'showconf': 'show the configurations',
            'run': 'run processing with configurations',
        }

    def showconf(self, argv):
        if (len(argv) != 1):
            print
            print "showconf <conf>"
            sys.exit(-1)
        cfgFile = argv[0]
        conf = cfg.Configuration()
        conf.addResources(cfgFile)
        proc = TxtProc(conf)
        print proc

    def process(self, argv):
        if (len(argv) != 1):
            print
            print "process <conf>"
            sys.exit(-1)
        cfgFile = argv[0]
        conf = cfg.Configuration()
        conf.addResources(cfgFile)
        proc = TxtProc(conf)
        proc.run()


