import re
import sys
import xml.etree.ElementTree as ET

import fileutils as fu
import importutils as iu

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

    def get(self, key, default=None, convertType=str):
        if self._dict.has_key(key):
            return convertType(self._subVar(self._dict[key]))
        else:
            return default

    def getStrings(self, key, default=[]):
        listStr = self.get(key, "")
        if listStr == None:
            return default
        strList = re.split('\s*,\s*', listStr)
        for i in range(len(strList)):
            strList[i] = self._subVar(strList[i])
        return strList

    def getIntRange(self, key, default=[]):
        listStr = self.get(key, "")
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
        clsName = self.get(key, None)
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

    def set(self, key, val):
        self._dict[key] = str(val)

    def write(self, filename):
        if filename.endswith('.xml'):
            writer = XmlConfigWriter()
            writer.write(self._dict, fu.normalizeName(filename))
        else:
            writer = PropConfigWriter()
            writer.write(self._dict, fu.normalizeName(filename))


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
        tree = ET.ElementTree(root)
        tree.write(filename)

class PropConfigWriter:
    def write(self, theDict, filename):
        f = open(fu.normalizeName(filename), 'w')
        for key, value in theDict.iteritems():
            f.write('%s = %s\n' %(key, value))
        f.close()

def main(infile, outfile):
    conf = Configuration()
    conf.addResources(infile)
    conf.set('tmp.dir', '/tmp')
    conf.set('local.dir', '${tmp.dir}/local')
    conf.set('num.modification', 3)
    print conf
    print conf.get('local.dir')
    print conf.get('num.modification', convertType=int)
    conf.set('str.list', '/data, /data/input , ${tmp.dir}, /data/soclj')
    conf.set('int.list', '1, 3, 5 , 4:8, 6:2:10')
    conf.write(outfile)
    print conf.getStrings('str.list')
    print conf.getIntRange('int.list')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

