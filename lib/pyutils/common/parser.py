"""
Parser.py

A object that has a parse() function
"""
import re
import shlex
import sys

from pyutils.common.clirunnable import CliRunnable

class Parser:
    def parse(self, obj):
        pass

    def __str__(self):
        return self.__name__

class KeyValParser(Parser):
    """
    KeyValParser:
        Parses a string with key and value pattern.

        pattern format {k:<key pattern>}<pattern>{v:<value pattern>}
        special indicator:
            %str, %numstr, %alpha, %lc, %uc, %name, %path, 
            %int, %long, %dec, %bin, %oct, %hex, %float.

    """
    SUPPORTED_TYPES = {
        '%str' : ('.+', str, 'any string'),
        '%numstr' : ('[0-9]+', str, 'number string'),
        '%alpha' : ('[a-zA-Z]+', str, 'alphabet'),
        '%lc' : ('[a-z]+', str, 'lower case'),
        '%uc' : ('[A-Z]+', str, 'upper case'),
        '%name' : ('[0-9a-zA-Z_-]+', str, 'regular name'),
        '%path' : ('[0-9a-zA-Z_-/]+', str, 'path name'),
        '%int' : ('[-+0-9]+', int, 'decimal'),
        '%long' : ('[-+0-9]+', long, 'decimal'),
        '%dec' : ('[-+0-9]+', int, 'decimal'),
        '%bin' : ('[-+01]+', int, 'binary'),
        '%oct' : ('[-+0-7]+', int, 'octal'),
        '%hex' : ('[-+0-9a-fA-F]+', int, 'hexadecimal'),
        '%float' : ('[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?', float, 'float'),
    }

    def __init__(self, pattern='{k:%str}\s*%:\s*{v:%str}'):
        keyPart = re.search('{k:(?P<key>[^}]+?)}', pattern).group('key')
        valPart = re.search('{v:(?P<val>[^}]+?)}', pattern).group('val')
        keyPattern, keyType = self.replTypeKey(keyPart)
        valPattern, valType = self.replTypeKey(valPart)
        pattern = re.sub('{k:[^}]+?}', '(?P<key>%s)'%keyPattern, pattern)
        pattern = re.sub('{v:[^}]+?}', '(?P<val>%s)'%valPattern, pattern)
        self.pattern = pattern
        self.keyType = keyType
        self.valType = valType

    def replTypeKey(self, pattern):
        for t in self.SUPPORTED_TYPES.keys():
            if t == pattern:
                return self.SUPPORTED_TYPES[t][0], self.SUPPORTED_TYPES[t][1]
        for t in self.SUPPORTED_TYPES.keys():
            if t in pattern:
                pattern = pattern.replace(t, self.SUPPORTED_TYPES[t][0])
        return pattern, str

    def parse(self, string):
        match = re.search(self.pattern, string)
        if match != None:
            key = self.keyType(match.group('key'))
            val = self.valType(match.group('val'))
            return key, val
        else:
            return None, None

    def __str__(self):
        return 'pattern:%s, keyType:%s, valType:%s' %(
            self.pattern, self.keyType, self.valType)

class CustomArgsParser():
    """
    CustomArgsParser:
        Parses args with customized option keys.

        Args and options are seperated by space. Strings within a pair of
        quotes are of the same arg or option. Only specified customized options
        are recognized and extracted. Other args are kept intact in order.
    """
    def __init__(self, optKeys=[], optFlags=[], defaults={}):
        self.optKeys = optKeys
        self.optFlags = optFlags
        self.options = defaults
        self.otherArgs = []

    def parse(self, args):
        while len(args) > 0:
            arg = args.pop(0)
            if arg in self.optKeys:
                self.options[arg] = args.pop(0)
            if arg in self.optFlags:
                self.options[arg] = True
            else:
                self.otherArgs.append(arg)

    def getOtherArgs(self):
        return self.otherArgs

    def getOption(self, key):
        if self.options.has_key(key):
            return self.options[key]
        elif key in self.optFlags:
            return False
        else:
            return None

    def getOptions(self):
        return self.options

class ParserRunnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'keyval' : 'KeyValParser',
        }

    def keyval(self, argv):
        if (len(argv) != 2):
            print "parser keyval <pattern> <string>"
            print
            sys.exit(-1)
        parser = KeyValParser(argv[0])
        print parser.parse(argv[1])

