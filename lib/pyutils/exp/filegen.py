import errno
import os
import re
import sys

from pyutils.common.clirunnable import CliRunnable
from pyutils.common.parse import CustomArgsParser

class FileGen(object):
    KEYWORDS = ['#outdir', '#params', '#file']
    WRITE_ALL_PARAMS_KEY = 'filegen.write.all.params'
    OUTDIR_KEY = 'filegen.outdir'
    ID_KEY = 'filegen.id'
    def __init__(self):
        self.outdir = None
        self.params = []
        self.files = {}

    def readgenconf(self, fn):
        """Read generation config file."""
        fh = open(fn, 'r')
        linebuf = []
        while True:
            line = fh.readline()
            if line == '':
                break
            line = line.strip()
            if line.endswith('\\'):
                #we encounter a continue mark
                shouldCont = True
                line = line.strip('\\')
                while shouldCont:
                    curr = fh.readline()
                    if curr == '':
                        raise SyntaxError(
                            'unexpected EOF while parsing continous line: %s'%line)
                    curr = curr.strip()
                    if not curr.endswith('\\'):
                        shouldCont = False
                    line += curr.strip('\\')
            if line.startswith('#'):
                for kw in FileGen.KEYWORDS:
                    if line.startswith(kw):
                        self.processLineBuf(linebuf)
                        assert len(linebuf) == 0, \
                                'Line buffer is not empty after process'
                        linebuf.append(line)
            else:
                linebuf.append(line)
        self.processLineBuf(linebuf)

    def processLineBuf(self, linebuf):
        if len(linebuf) == 0:
            return
        first = linebuf[0]
        if first.startswith('#outdir'):
            self.processOutdir(linebuf)
        elif first.startswith('#params'):
            self.processParams(linebuf)
        elif first.startswith('#file'):
            self.processFile(linebuf)

    def processOutdir(self, linebuf):
        linebuf.pop(0)
        while len(linebuf) != 0:
            line = linebuf.pop(0)
            line = line.strip()
            if line != '':
                if self.outdir is None:
                    self.outdir = line
                else:
                    raise SyntaxError(
                        'Multiple definition of #outdir, previous:%s'%self.outdir)

    def processParams(self, linebuf):
        consts, varconf, subs = self.readParamConfigs(linebuf)
        for varset in self.genvars(varconf):
            varset.update(consts)
            self.subvars(varset, subs)
            self.params.append(varset)

    def readParamConfigs(self, linebuf):
        consts = {}
        varconf = {}
        subs = {}
        while len(linebuf) != 0:
            line = linebuf.pop(0)
            if line.startswith('#'):
                continue
            line = line.strip()
            if line == '':
                continue
            key, val = line.split('=')
            key = key.strip()
            val = val.strip()
            if key.startswith('const'):
                key = key.split('const')[1].strip()
                val = eval(val)
                consts[key] = val
            elif key.startswith('var'):
                key = key.split('var')[1].strip()
                val = eval(val)
                varconf[key] = val
            elif key.startswith('sub'):
                key = key.split('sub')[1].strip()
                subs[key] = val
            else:
                raise SyntaxError(
                    'Unrecognizable prefix in #params section: %s'%key)
        return consts, varconf, subs

    def genvars(self, varconf):
        """Generate variables from varconf."""
        total = 1
        for v in varconf.values():
            total *= len(v)
        count = 0
        keys = varconf.keys()
        indices = [0] * len(keys)
        while count < total:
            currvars = {}
            for i, key in enumerate(keys):
                if ',' not in key:
                    val = varconf[key][indices[i]]
                    currvars[key] = val
                else:
                    #we have a form of key1, key2 = [(val11, val2), (val21, val22), ...]
                    val = varconf[key][indices[i]]
                    for j, subkey in enumerate(key.split(',')):
                        subkey = subkey.strip()
                        currvars[subkey] = val[j]
            yield currvars
            count += 1
            indices[0] += 1
            if indices[0] == len(varconf[keys[0]]):
                indices[0] = 0
                for i in range(1, len(keys)):
                    indices[i] += 1
                    if indices[i] < len(varconf[keys[i]]):
                        break
                    indices[i] = 0

    def subvars(self, params, subs):
        subre = re.compile('@[a-zA-Z0-9.]+')
        for key, val in subs.iteritems():
            assert '@' in val
            while '@' in val:
                match = subre.search(val)
                if match is None:
                    raise SyntaxError('%s is not expandable' %val)
                subname = match.group()
                subkey = subname.lstrip('@')
                if not subkey in params:
                    raise SyntaxError(
                        'Unknown expand name: %s. '
                        'Possibly because multi-reference is not allowed' %(subkey))
                val = re.sub(subname, str(params[subkey]), val)
            params[key] = val

    def processFile(self, linebuf):
        line = linebuf.pop(0)
        splits = line.split(' ')
        if len(splits) != 2:
            raise SyntaxError('Wrong format at %s'%line)
        filename = splits[1].strip()
        contents = []
        while len(linebuf) != 0:
            contents.append(linebuf.pop(0))
        if filename in self.files:
            raise ValueError('File name appeared before %s'%filename)
        self.files[filename] = contents

    def generate(self, fn):
        self.readgenconf(fn)
        if self.outdir is None:
            raise SyntaxError('#outdir is not specified')
        if len(self.params) == 0:
            raise SyntaxError('#params is not specified')
        if len(self.files) == 0:
            self.files['__config__'] = ['@' + FileGen.WRITE_ALL_PARAMS_KEY]
        self.mkdir_p(self.outdir)
        for i, params in enumerate(self.params):
            outdir = '%s/%s'%(self.outdir, i)
            self.mkdir_p(outdir)
            params[FileGen.OUTDIR_KEY] = outdir
            params[FileGen.ID_KEY] = i
            for name, contents in self.files.iteritems():
                outname = '%s/%s'%(outdir, name)
                fh = open(outname, 'w')
                for content in contents:
                    if '@' + FileGen.WRITE_ALL_PARAMS_KEY in content:
                        self.writeParams(fh, params)
                    else:
                        new = self.subContent(content, params)
                        fh.write(new)
                        fh.write('\n')
                fh.close()

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def writeParams(self, fh, params):
        fh.write('\n')
        for key, val in params.iteritems():
            fh.write('%s = %s\n' %(key, val))
        fh.write('\n')

    def subContent(self, content, params):
        subre = re.compile('@[a-zA-Z0-9.]+')
        string = content
        ret = content
        while '@' in string:
            match = subre.search(string)
            if match is None:
                break
            subname = match.group()
            subkey = subname.lstrip('@')
            if not subkey in params:
                continue
            ret = re.sub(subname, str(params[subkey]), ret)
            string = string[string.index('@') + 1:]
        return ret

class FileGenCli(CliRunnable):

    def __init__(self):
        self.availableCommand = {
            'example': 'show an example of config file',
            'keywords': 'show a list of keywords',
            'generate': 'generate from config file',
        }

    def example(self, argv):
        print '#outdir'
        print '/tmp/pyutilfilegen'
        print '#params'
        print 'const a = 1'
        print 'var b = [1,2,3]'
        print 'var c, d = [(1, 2), (2, 3)]'
        print 'sub e = @a'
        print '#file config'
        print '@filegen.write.all.params'
        print '#file self'
        print '@filegen.outdir'
        print '@filegen.id'

    def keywords(self, argv):
        print FileGen.KEYWORDS
        print FileGen.WRITE_ALL_PARAMS_KEY
        print FileGen.OUTDIR_KEY
        print FileGen.ID_KEY

    def generate(self, argv):
        if (len(argv) != 1):
            print
            print 'generate <config file>'
            sys.exit(-1)
        FileGen().generate(argv[0])

###### TEST #####
def test():
    cfgstrings = [
        '#outdir\n',
        '/tmp/pyutilfilegen\n',
        '\n',
        '#params\n',
        'const num.zones = 1\n',
        'const num.storage.nodes.per.zone = 1\n',
        'const network.sim.class = "network.FixedLatencyNetwork"\n',
        'const fixed.latency.nw.within.zone = 5\n',
        'const fixed.latency.nw.cross.zone = 5\n',
        'const txn.gen.impl = "txngen.UniformTxnGen"\n',
        'const total.num.txns = 10000\n',
        'const txn.arrive.interval.dist = ("expo", 10, )\n',
        'const simulation.duration = 600000\n',
        'var nwrites = [8, 12]\n',
        'var intvl = [10, 20]\n',
        'var x, y = [(1, 2), (2, 4)]\n',
        'sub txn.classes = [{"freq":1, "nwrites":@nwrites, "intvl.dist":("expo", @intvl,)}]\n',
        '\n',
        '#file config\n',
        '@filegen.write.all.params',
        '\n',
        '#file logcfg\n',
        '[handler_consoleHandler]\n',
        'class=StreamHandler\n',
        'level=INFO\n',
        'formatter=default\n',
        'args=(sys.stdout,)\n',
        '\n',
        '[handler_fileHandler]\n',
        'class=FileHandler\n',
        'level=DEBUG\n',
        'formatter=default\n',
        "args=('@filegen.outdir', 'w')\n",
    ]
    fh = open('/tmp/config', 'w')
    fh.writelines(cfgstrings)
    fh.close()
    FileGen().generate('/tmp/config')

def main():
    test()

if __name__ == '__main__':
    main()

