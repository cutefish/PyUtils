"""
Parser.py

A object that has a parse() function
"""
import re

class Parser:
    def parse(self, obj):
        pass

class KeyValParser(Parser):

    SUPPORTED_TYPES = {
        '%str' : ('.+', str, 'any string'),
        '%numstr' : ('[0-9]+', str, 'number string'),
        '%alpha' : ('[a-zA-Z]+', str, 'alphabet'),
        '%lc' : ('[a-z]+', str, 'lower case'),
        '%uc' : ('[A-Z]+', str, 'upper case'),
        '%name' : ('[a-zA-Z_-]+', str, 'regular name'),
        '%path' : ('[a-zA-Z_-/]+', str, 'path name'),
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




