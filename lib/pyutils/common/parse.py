"""
parse.py

A object that has a parse() function
"""
import re
import shlex
import sys

from pyutils.common.clirunnable import CliRunnable

class KeyValParser(object):
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
        '%name' : ('[0-9a-zA-Z-._]+', str, 'regular name'),
        '%path' : ('[0-9a-zA-Z-._/]+', str, 'path name'),
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

class CustomArgsParser(object):
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
        self.posArgs = []

    def parse(self, args):
        while len(args) > 0:
            arg = args.pop(0)
            if arg in self.optKeys:
                self.options[arg] = args.pop(0)
            if arg in self.optFlags:
                self.options[arg] = True
            else:
                self.posArgs.append(arg)

    def getPosArgs(self):
        return self.posArgs

    def getPosArg(self, idx):
        return self.posArgs[idx]

    def getOption(self, key, default=None):
        if self.options.has_key(key):
            return self.options[key]
        elif key in self.optFlags:
            return False
        else:
            return default

    def getOptions(self):
        return self.options

def str2msec(string):
    if string.endswith('year'):
        num = float(string[0:-4])
        factor = 1000 * 60 * 60 * 24 * 365
    elif string.endswith('mon'):
        num = float(string[0:-3])
        factor = 1000 * 60 * 60 * 24 * 30
    elif string.endswith('day'):
        num = float(string[0:-3])
        factor = 1000 * 60 * 60 * 24
    elif string.endswith('hour'):
        num = float(string[0:-4])
        factor = 1000 * 60 * 60
    elif string.endswith('min'):
        num = float(string[0:-3])
        factor = 1000 * 60
    elif string.endswith('sec'):
        num = float(string[0:-3])
        factor = 1000
    else:
        num = float(string)
        factor = 1
    return num * factor

def str2bytes(string):
    if string.endswith('T') or string.endswith('t'):
        num = float(string[0:-1])
        factor = 1024 * 1024 * 1024 * 1024
    if string.endswith('G') or string.endswith('g'):
        num = float(string[0:-1])
        factor = 1024 * 1024 * 1024 
    if string.endswith('M') or string.endswith('m'):
        num = float(string[0:-1])
        factor = 1024 * 1024 
    if string.endswith('K') or string.endswith('k'):
        num = float(string[0:-1])
        factor = 1024 
    else:
        num = float(string[0:-1])
        factor = 1
    return num * factor

class LinesPattern(object):
    """A lines pattern matches several lines in text.

    If all the regex(s) in the label matches lines in order, then the label
    matches the context.
    """
    def __init__(self, regexps):
        self.regexps = []
        if isinstance(regexps, str):
            regexps = regexps.split(';')
        for regexp in regexps:
            self.regexps.append(re.compile(regexp))

    def match(self, lines):
        for i, line in enumerate(lines):
            if self.regexp[i].search(line):
                return False
        return True

class RecordsContext(object):
    """A record context is the start and end lines pattern of a record.

    A record can have nested records. Vulnerable records are prone to be
    incomplete which will lack start or end context marks.
    """
    def __init__(self, start, end, name=None, faultTol=False):
        if name is None:
            self.name = '(%s, %s)'%(str(start), str(end))
        else:
            self.name = name
        self.start = start
        self.end = end
        self.supctx = None
        self.subctxs = []
        self.faultTol = faultTol

    def isStart(self, lines):
        """Start pattern marks the start of a record."""
        self.start.match(lines)

    def isEnd(self, lines):
        """End pattern marks the end of a record.

        Start or end pattern of super contexts marks the end of this record if
        it can be fault tolarant.
        """
        if self.end.match(lines) is True:
            return True
        if self.faultTol:
            curr = self.supctx
            while curr is not None:
                if curr.isStart(lines) or curr.isEnd(lines):
                    return True

    def enclose(self, subctx):
        subctx.supctx = self
        self.subctxs.append(subctx)

    def __str__(self):
        queue = [self]
        retstrings = []
        while len(queue) != 0:
            ctx = queue.pop(0)
            if ctx.supctx is None:
                supname = None
            else:
                supname = ctx.supctx.name
            retstrings.append('(%s->%s : %s==>%s, %s)' 
                              %(ctx.name, supname,
                                ctx.start, ctx.end, ctx.faultTol))
            for subctx in ctx.subctxs:
                queue.append(subctx)
        return ', '.join(retstrings)

    @classmethod
    def parse(cls, source, sourceType):
        """Parse records context from string or file.

        Parse Format:
            Parses by lines.
            Enclosue mark is specified using 'encl.mark=%s'.
            Each line starts with the encl.mark and is in the form:
                context = encl.level[name] | start.lines.pattern | end.lines.pattern | faultTol
                encl.level = [encl.mark]+
                lines.pattern = 1st line pattern ; 2nd line pattern; ...
            Upper line contexts enclose lower line contexts if encl.level increase 1.

        Example:
            encl.mark=#
            #|#experiments
            ##description | Description
            ##index | ###; INDEX START; ### | ###; INDEX END; ###
            #|#data
            ##|### FILE ###|
        """
        if sourceType == 'string':
            return cls.parseLines(source.splitlines())
        elif sourceType == 'lines':
            return cls.parseLines(source)
        elif sourceType == 'file':
            fh = source
            if not isinstance(fh, file):
                fh = open(source, 'r')
            return cls.parseLines(fh.readlines())

    @classmethod
    def parseLines(cls, lines):
        #get mark
        while True:
            if len(lines) == 0:
                raise EOFError('Cannot find mark line encl.mark=?')
            line = lines.pop(0)
            if 'encl.mark' in line:
                key, mark = line.split('=')
                mark = mark.strip()
                break
            continue
        #parsing
        context = RecordsContext(None, None, 'root')
        currLevel = 0
        currCtx = context
        while True:
            if len(lines) == 0:
                break
            line = lines.pop(0)
            if not line.startswith(mark):
                continue
            levelString, start, end, faultTol = cls.splitLine('\|', line)
            level, name = cls.parseLevelString(levelString, mark)
            if level > currLevel + 1:
                raise SyntaxError('Context level missing: super=(%s, %s), curr=(%s, %s)'
                                  %(currLevel, context.name, level, name))
            elif level == currLevel + 1:
                sub = RecordsContext(start, end, name, faultTol)
                currCtx.enclose(sub)
                currLevel = level
                currCtx = sub
            elif level == currLevel:
                sib = RecordsContext(start, end, name, faultTol)
                currCtx.supctx.enclose(sib)
                currCtx = sub
            else:
                for i in range(currLevel - level + 1):
                    currCtx = currCtx.supctx
                sib = RecordsContext(start, end, name, faultTol)
                currCtx.enclose(sib)
                currLevel = level
                currCtx = sib
        cls.checkContext(context)
        return context

    @classmethod
    def splitLine(cls, pattern, string):
        #fill None for '' pattern or missing pattern
        result = re.split(pattern, string)
        numFills = 4 - len(result)
        for i in range(numFills):
            result.append(None)
        if numFills > 0:
            result[-1] = False
        for i, r in enumerate(result):
            if r == '':
                result[i] = None
        return result

    @classmethod
    def parseLevelString(cls, string, mark):
        level = string.count(mark)
        blank, name = string.split(mark * level)
        name = name.strip()
        if name == '':
            name = None
        return level, name

    @classmethod
    def checkContext(cls, context):
        queue = [context]
        while len(queue) != 0:
            ctx = queue.pop(0)
            if ctx.name != 'root':
                if ctx.start is None and ctx.end is None:
                    raise SyntaxError('context %s has None start and end' %ctx)
            if len(ctx.subctxs) > 1:
                for subctx in ctx.subctxs:
                    if subctx.start is None:
                        raise SyntaxError(
                            'sibling context must start pattern: %s' %subctx)
            for subctx in ctx.subctxs:
                queue.append(subctx)

class ParseRunnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'keyval' : 'KeyValParser',
        }

    def keyval(self, argv):
        if (len(argv) != 2):
            print "parse keyval <pattern> <string>"
            print
            sys.exit(-1)
        parser = KeyValParser(argv[0])
        print parser.parse(argv[1])

### TEST ###
def testContextParse():
    lines = ['encl.mark=#',
             '#|experiments',
             '##description | Description',
             '##index | ###; INDEX START; ### | ###; INDEX END; ###',
             '#|data',
             '##|### FILE ###|',
            ]
    print RecordsContext.parse(lines, 'lines')

def main():
    testContextParse()

if __name__ == '__main__':
    main()
