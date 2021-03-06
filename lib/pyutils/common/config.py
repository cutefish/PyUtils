import re
import sys
import xml.etree.ElementTree as ET

import pyutils.common.fileutils as fu
import pyutils.common.importutils as iu

from pyutils.common.clirunnable import CliRunnable

class Configuration:
    VAR_MATCH = '\$\{[^}$\s]+\}'

    def __init__(self):
        self._dict = {}

    def addResources(self, resList):
        if not isinstance(resList, list):
            resList = [resList]
        for res in resList:
            self._addResource(res)

    def _addResource(self, res):
        if isinstance(res, Configuration):
            self._dict.update(res._dict)
        elif (isinstance(res, str) and res.endswith('.xml')):
            parser = XmlConfigParser()
            self._dict = parser.parse(res)
        elif (isinstance(res, str) and
              (res.endswith('.properties') or
               res.endswith('.prop'))):
            parser = PropConfigParser()
            self._dict = parser.parse(res)

    def getv(self, key, default=None, convertType=str):
        if self._dict.has_key(key):
            return convertType(self._subVar(self._dict[key]))
        else:
            return default

    def getStrings(self, key, default=[]):
        listStr = self.getv(key, "")
        if listStr == None:
            return default
        strList = re.split('\s*,\s*', listStr)
        for i in range(len(strList)):
            strList[i] = self._subVar(strList[i])
        return strList

    def getIntRange(self, key, default=[]):
        listStr = self.getv(key, "")
        if listStr == None:
            return default
        strList = re.split('\s*,\s*', listStr)
        ret = set([])
        for s in strList:
            if ':' in s:
                linspace = re.split('\s*:\s*', s)
                start = int(linspace[0])
                end = int(linspace[-1])
                if len(linspace) == 3:
                    step = int(linspace[1])
                else:
                    step = 1
                for i in range(start, end, step):
                    ret.add(i)
            else:
                ret.add(int(s))
        return sorted(ret)

    def getClass(self, key, default=None, path=[]):
        clsName = self.getv(key, None)
        if clsName == None:
            return default
        try:
            cls = iu.loadClass(clsName, path)
            return cls
        except ImportError as ie:
            print ie
            return default

    def _subVar(self, var):
        match = re.match(self.VAR_MATCH, var)
        if match == None:
            return var
        key = match.group().strip('${').strip('}')
        if not self._dict.has_key(key):
            return var
        val = self._dict[key]
        return re.sub(self.VAR_MATCH, val, var)

    def setv(self, key, val):
        self._dict[key] = str(val)

    def write(self, filename):
        if filename.endswith('.xml'):
            writer = XmlConfigWriter()
            writer.write(self._dict, fu.normalizeName(filename))
        else:
            writer = PropConfigWriter()
            writer.write(self._dict, fu.normalizeName(filename))

    def iteritems(self):
        return self._dict.iteritems()


    def __str__(self):
        return str(self._dict)


class XmlConfigParser:
    def parse(self, filename):
        retDict = {}
        tree = ET.parse(fu.normalizeName(filename))
        root = tree.getroot()
        if 'configuration' != root.tag:
            raise ValueError('invalid root tag: ' + root.tag)
        for prop in root:
            if 'configuration' == prop.tag:
                retDict.update(self.parse(prop.text))
                continue
            if 'property' != prop.tag:
                raise ValueError('invalid property tag: ' + prop.tag)
            key = None
            val = None
            for field in prop:
                if 'name' == field.tag:
                    #name should not have child
                    if len(list(field)) != 0:
                        raise SyntaxError('name should not have child:'
                                          '%s' %ET.dump(field))
                    key = field.text
                if 'value' == field.tag:
                    #value should not have child
                    if len(list(field)) != 0:
                        raise SyntaxError('value should not have child:'
                                          '%s' %ET.dump(field))
                    val = field.text
            if (key == None) or (val == None):
                raise SyntaxError('no key or value for prop:'
                                  '%s' %ET.dump(prop))
            retDict[key] = val
        return retDict

class PropConfigParser:
    def parse(self, filename):
        retDict = {}
        f = open(fu.normalizeName(filename))
        lineno = 1
        for line in f:
            if line.startswith('#'):
                continue
            try:
                key, value = re.split('\s*=\s*', line.strip(), 1)
            except:
                print "PropConfigParser Parse Error. [%s] %s" %(lineno, line)
                continue
            retDict[key] = value
        f.close()
        return retDict

class XmlConfigWriter:
    def write(self, theDict, filename):
        root = ET.Element('configuration')
        root.text = '\n  \n  '
        lastProp = None
        for key in theDict:
            prop = ET.SubElement(root, 'property')
            prop.text = '\n    '
            prop.tail = '\n  \n  '
            name = ET.SubElement(prop, 'name')
            name.text = key
            name.tail = '\n    '
            value = ET.SubElement(prop, 'value')
            value.text = theDict[key]
            value.tail = '\n  '
            lastProp = prop
        lastProp.tail = '\n\n'
        root.tail = '\n'
        tree = ET.ElementTree(root)
        tree.write(filename)

class PropConfigWriter:
    def write(self, theDict, filename):
        f = open(fu.normalizeName(filename), 'w')
        for key, value in theDict.iteritems():
            f.write('%s = %s\n' %(key, value))
        f.close()

class ConfigCli(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'getv' : 'get a property to configuration file',
            'setv' : 'set a property to configuration file',
        }

    def getv(self, argv):
        if (len(argv) != 2):
            print
            print "config get <xml file> <name0;name1;...>"
            sys.exit(-1)
        conf = Configuration()
        conf.addResources(argv[0])
        for key in argv[1].split(';'):
            print key, conf.getv(key.strip())

    def setv(self, argv):
        if (len(argv) != 2):
            print
            print "config set <xml file> <name0,value0;...>"
            sys.exit(-1)
        conf = Configuration()
        conf.addResources(argv[0])
        for keyvalue in argv[1].split(';'):
            key, value = keyvalue.split(',')
            key = key.strip()
            value = value.strip()
            conf.setv(key, value)
        conf.write(argv[0])

def main(infile, outfile):
    conf = Configuration()
    conf.addResources(infile)
    conf.setv('tmp.dir', '/tmp')
    conf.setv('local.dir', '${tmp.dir}/local')
    conf.setv('num.modification', 3)
    print conf
    print conf.getv('local.dir')
    print conf.getv('num.modification', convertType=int)
    conf.setv('str.list', '/data, /data/input , ${tmp.dir}, /data/soclj')
    conf.setv('int.list', '1, 3, 5 , 4:8, 6:2:10')
    conf.write(outfile)
    print conf.getStrings('str.list')
    print conf.getIntRange('int.list')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

