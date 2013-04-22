"""
ptree.py

PropertyTree data structure for experiments
"""

import pickle
import re
import sys
import traceback

from pyutils.common.clirunnable import CliRunnable

class TreeNode(object):
    """ Property tree node. """
    def __init__(self, key, val, children=None):
        self._key = key
        self._val = val
        self._children = children
        if self._children == None:
            self._children = []

    @property
    def key(self):
        return self._key

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, other):
        self._val = other

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, other):
        self._children = other

    def hasChild(self):
        return len(self._children) != 0

    def __str__(self):
        ret = []
        ret.append(self._key + "->[")
        for child in self._children:
            ret.append(child.key + ", ")
        ret.append("]")
        return ''.join(ret)


class PropertyTree(object):
    """
    
    A simplified mimicry of boost property tree.

    "The Property Tree library provides a data structure that stores an
    arbitrarily deeply nested tree of values, indexed at each level by some
    key. Each node of the tree stores its own value, plus an ordered list of
    its subnodes and their keys. The tree allows easy access to any of its
    nodes by means of a path, which is a concatenation of multiple keys."(copy
    from boost)

    """
    def __init__(self, sep="."):
        self.root = TreeNode("", None)
        self.sep = sep
        self.innerkeyRe = '[a-zA-Z0-9-_]+'
        self.validRe = re.compile('^(\%s?%s)+$'%(self.sep, self.innerkeyRe))

    def normalizeKey(self, key):
        #remove repeated '.'
        key = re.sub('(\.\.)+', '.', key)
        if not self.validRe.match(key):
            raise KeyError("Bad key: " + key)
        return key.strip(self.sep)

    def splitKey(self, key):
        """ Split key into parent and child. """
        if not self.sep in key:
            return "", key
        lastSepIndex = key.rindex(self.sep)
        parent = key[0:lastSepIndex]
        child = key[lastSepIndex + 1:]
        return parent, child

    def compareKey(self, key1, key2):
        """ Compare key and return common part and the rest. """
        levelKeys1 = key1.split(self.sep)
        levelKeys2 = key2.split(self.sep)
        minLevel = min(len(levelKeys1), len(levelKeys2))
        common = []
        for i in range(minLevel):
            if (levelKeys1[i] != levelKeys2[i]):
                break
            common.append(levelKeys1[i])
        commonKey = self.sep.join(common)
        rest1 = re.sub(commonKey, '', key1).lstrip(self.sep)
        rest2 = re.sub(commonKey, '', key2).lstrip(self.sep)
        return commonKey, rest1, rest2

    def _dive(self, key, node, create=False):
        if key == "":
            return node
        levelKeys = key.strip(self.sep).split(self.sep)
        curr = node
        currKey = ""
        for i in range(len(levelKeys)):
            next = None
            currKey = levelKeys[i]
            for child in curr.children:
                if child.key == currKey:
                    next = child
                    break
            if next == None:
                if not create:
                    raise KeyError("Key not found: %s, %s" %(key, currKey))
                else:
                    next = TreeNode(currKey, None)
                    curr.children.append(next)
            curr = next
        return curr

    def find(self, key):
        """ Find the TreeNode matching the key.

        Return the node if found. Otherwise throw KeyError.

        """
        key = self.normalizeKey(key)
        return self._dive(key, self.root)

    def add(self, key, val, overwrite=True):
        """ Add the TreeNode matching the key.  

        Return the added TreeNode.
        If key exists and overwrite is False, raise KeyError.
        
        """
        key = self.normalizeKey(key)
        parentKey, childKey = self.splitKey(key)
        parent = self._dive(parentKey, self.root, create=True)
        curr = None
        for child in parent.children:
            if child.key == childKey:
                if not overwrite:
                    raise KeyError("Key already exists: " + key)
                curr = child
        if curr == None:
            curr = TreeNode(childKey, val)
            parent.children.append(curr)
        else:
            curr.val = val
        return curr

    def remove(self, key):
        """ Remove the TreeNode matching the key. 

        Return True if existed. False otherwise.
        
        """
        key = self.normalizeKey(key)
        parentKey, childKey = self.splitKey(key)
        try:
            parent = self._dive(parentKey, self.root, create=False)
        except KeyError:
            return False
        for child in parent.children:
            if child.key == childKey:
                parent.children.remove(child)
                return True
        return False

    def _dfsKey(self, key, node):
        queue = []
        queue.append((node, ""))
        ret = []
        while len(queue) != 0:
            curr, fullKey = queue.pop()
            if curr.key == key:
                ret.append((curr, fullKey.strip(self.sep)))
            for child in curr.children:
                queue.append((child, fullKey + self.sep + child.key))
        return ret

    def _findLeaves(self, node):
        queue = []
        queue.append((node, ""))
        ret = []
        while len(queue) != 0:
            curr, fullKey = queue.pop()
            if not curr.hasChild():
                ret.append((curr, fullKey.strip(self.sep)))
            for child in curr.children:
                queue.append((child, fullKey + self.sep + child.key))
        return ret

    def _extractGroupKey(self, pattern, fullKey):
        if not '[' in pattern:
            return fullKey
        psplit = pattern.split(self.sep)
        ksplit = fullKey.split(self.sep)
        ppos = 0
        kpos = 0
        groupKeys = []
        while ppos < len(psplit):
            key = psplit[ppos]
            if key == '[':
                groupKeys.append(ksplit[kpos])
            elif key == '*':
                pass
            elif key == '**' or key == '[[':
                ppos += 1
                kpos += 1
                extracted = [ksplit[kpos - 1]]
                if (ppos == len(psplit)):
                    if key == '[[':
                        extracted = ksplit[kpos - 1:]
                        groupkey = self.sep.join(extracted)
                        groupKeys.append(groupkey)
                    break
                nextKey = psplit[ppos]
                while kpos < len(ksplit):
                    if ksplit[kpos] == nextKey:
                        break
                    else:
                        if key == '[[':
                            extracted.append(ksplit[kpos])
                        kpos += 1
                if len(extracted) != 0:
                    groupkey = self.sep.join(extracted)
                    if key == '[[':
                        groupKeys.append(groupkey)
            else:
                if psplit[ppos] != ksplit[kpos]:
                    raise KeyError("key not match pattern." +
                                   " key=" + fullKey +
                                   " pattern=" + pattern)
            ppos += 1
            kpos += 1
        return tuple(groupKeys)

    def match(self, pattern):
        """ Search for all nodes matching the wildcard pattern.
        
        Pattern is a combination of inner keys and special charactors, for
        example, spam.egg.*.[.**

        Special charactor:
            *   --  wild card for matching one inner key
            **  --  wild card for aggresively matching all keys
            [   --  group using this inner key
            [[  --  group using wild card

        """
        #normalize: remove repeated sep, add leading sep and remove repeated **
        pattern = re.sub('(\*\*\.)+','**.', pattern)
        pattern = re.sub('(\.\.)+', '.', pattern)
        pattern = pattern.strip(self.sep)
        #group keys
        levelKeys = pattern.split(self.sep)
        keys = []
        prevstop = 0
        for i in range(len(levelKeys)):
            validRe = re.compile('^(\*{1,2}|\[{1,2}|%s)$' %self.innerkeyRe)
            if not validRe.match(levelKeys[i]):
                raise KeyError("Bad pattern: " + pattern +
                               " at innterkey:" + levelKeys[i])
            if (levelKeys[i] == '**' or levelKeys[i] == '[[') \
               and i < len(levelKeys) - 1:
                if levelKeys[i + 1] == '*' or levelKeys[i + 1] == '[':
                    raise KeyError(
                        "Bad key: " + key +
                        "[ and * cannot follow ** or [[")
            if levelKeys[i] == '*' or levelKeys[i] == '[':
                prev = self.sep.join(levelKeys[prevstop:i])
                if prev != "":
                    keys.append(prev)
                keys.append(levelKeys[i])
                prevstop = i + 1
            if levelKeys[i] == '**' or levelKeys[i] == '[[':
                prev = self.sep.join(levelKeys[prevstop:i])
                if prev != "":
                    keys.append(prev)
                keys.append(levelKeys[i])
                if i < len(levelKeys) - 1:
                    keys.append(levelKeys[i + 1])
                prevstop = i + 2
            if i == len(levelKeys) - 1:
                prev = self.sep.join(levelKeys[prevstop : i + 1])
                if prev != "":
                    keys.append(prev)
        #foreach key, if its a wildcard, then search, otherwise, dive
        queue = []
        nodes = {}
        queue.append((self.root, "", 0))
        while len(queue) != 0:
            curr, fullKey, index = queue.pop()
            fullKey = fullKey.strip(self.sep)
            if index == len(keys):
                #if we exhaust the matching pattern, put into nodes
                groupKey = self._extractGroupKey(pattern, fullKey)
                if not nodes.has_key(groupKey):
                    nodes[groupKey] = []
                nodes[groupKey].append((fullKey, curr))
                continue
            nextKey = keys[index]
            if (nextKey == '*' or nextKey == '['):
                #a wild card place holder, queue all children
                for child in curr.children:
                    queue.append(
                        (child, fullKey + self.sep + child.key, index + 1))
            elif (nextKey == '**' or nextKey == '[['):
                #nextKey is **, find the descendant parents matching the first
                index = index + 1
                if index == len(keys):
                    #if we exhaust the matching pattern, put all leaf into nodes
                    leaves = self._findLeaves(curr)
                    for leaf, leafKey in leaves:
                        leafKey = fullKey + self.sep + leafKey
                        groupKey = self._extractGroupKey(pattern, leafKey)
                        if not nodes.has_key(groupKey):
                            nodes[groupKey] = []
                        nodes[groupKey].append((leafKey, leaf))
                    continue
                nextKey = keys[index]
                for next, key in self._dfsKey(nextKey, curr):
                    queue.append(
                        (next, fullKey +self.sep + key, index + 1))
            else:
                #regular key, directly find the next node
                try:
                    next = self._dive(nextKey, curr, create=False)
                    fullKey = fullKey + self.sep + nextKey
                    index = index + 1
                    queue.append((next, fullKey, index))
                except KeyError:
                    #key not found, this path is dead
                    pass
        return nodes

    def prefix(self, prefix):
        """ Prefix the tree. """
        prefix = self.normalizeKey(prefix)
        children = []
        for child in self.root.children:
            children.append(child)
        self.root.children = []
        leaf = self.add(prefix, None)
        for child in children:
            leaf.children.append(child)
        return self

    def include(self, ptree):
        """ Include another ptree. 

        Common absolute keys will be merged onto the same path.

        """
        queue = []
        queue.append((self.root, ptree.root))
        while (len(queue) > 0):
            this, other = queue.pop()
            for otherChild in other.children:
                common = False
                for thisChild in this.children:
                    if thisChild.key == otherChild.key:
                        queue.append((thisChild, otherChild))
                        common = True
                        break
                if not common:
                    this.children.append(otherChild)

    def getv(self, key, keepKeys=False):
        if not ('*' in key or '[' in key):
            try:
                node = self.find(key)
                return node.val
            except KeyError:
                return None
        else:
            keyvals = {}
            for groupkey, nodes in self.match(key).iteritems():
                if keepKeys:
                    vals = {}
                else:
                    vals = []
                for elem in nodes:
                    fullKey, node = elem
                    if keepKeys:
                        vals[fullKey] = node.val
                    else:
                        vals.append(node.val)
                keyvals[groupkey] = vals
            return keyvals

    def setv(self, key, val):
        self.add(key, val, True)

    @staticmethod
    def dump(tree, f):
        fd = open(f, 'w')
        pickle.dump(tree, fd)

    @staticmethod
    def load(f):
        fd = open(f, 'r')
        tree = pickle.load(fd)
        return tree

    @staticmethod
    def merge(ptrees, sep='.'):
        newtree = PropertyTree(sep)
        for ptree in ptrees:
            newtree.include(ptree)
        return newtree

    def __str__(self):
        """Retrun all the keys and values."""
        queue=[]
        queue.append((self.root, self.root.key))
        ret = []
        while len(queue) != 0:
            curr, fullKey = queue.pop()
            if not curr.hasChild():
                ret.append(fullKey.strip(self.sep) + ": " + str(curr.val))
                continue
            for child in curr.children:
                queue.append((child, fullKey + self.sep + child.key))
        return '\n'.join(ret)

def testPropertyTree():
    pt = PropertyTree()
    pt.add("test.a.0", 1)
    pt.add("test.b", 2)
    pt.add("plan.summary", "A plan")
    pt.add("plan.iter.job.exec.time", 10)
    pt.add("plan0.iter0.job0.exec.time", 10)
    pt.add("plan0.iter0.job0.num.data.locals", 15)
    pt.add("plan0.iter0.job0.num.rack.locals", 20)
    pt.add("plan0.iter0.job0.mapper.0.exec.time", 3)
    pt.add("plan0.iter0.job0.mapper.0.read.type", "dfs")
    pt.add("plan0.iter0.job0.mapper.1.exec.time", 2)
    pt.add("plan0.iter0.job0.mapper.1.read.type", "cache")
    pt.add("plan0.iter0.job1.mapper.1.read.type", "cache")
    pt.add("plan0.iter0.job1.mapper.1.exec.time", 2)
    pt.add("plan0.iter0.job1.mapper.0.read.type", "dfs")
    pt.add("plan0.iter0.job1.mapper.0.exec.time", 3)
    pt.add("plan0.iter0.job1.num.rack.locals", 20)
    pt.add("plan0.iter0.job1.num.data.locals", 15)
    pt.add("plan0.iter0.job1.exec.time", 10)
    print pt
    print
    pt.remove("test")
    pt.remove("plan.iter")
    print pt
    print
    print pt.getv("plan0.iter0.job1.num.data.locals")
    pt.setv("plan.summary", "A plan for test")
    print pt
    print pt.getv("plan0.iter0.job0.mapper.0.**")
    print pt.getv("plan0.iter0.job0.mapper.*.exec.time")
    print pt.getv("*.mapper.*.read.type")
    print pt.getv("**.mapper.*.read.type")
    print
    PropertyTree.dump(pt, '/tmp/testpt')
    pt = PropertyTree.load('/tmp/testpt')
    print pt
    print pt.getv("plan0.iter0.job0.mapper.0.**")
    print pt.getv("plan0.iter0.job0.mapper.*.exec.time")
    print pt.getv("**.mapper.*.read.type")

    print pt.getv("*.*.[.mapper.**", True)
    print pt.getv("*.*.[.mapper.[.**", True)

    print pt.getv("*.*.[.mapper.[[")
    print pt.getv("*.*.[.mapper.[.[[")
    print pt.getv("[[.mapper.**")

class PTreeRunnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'load' : 'show a property tree dump file',
            'interact' : 'open a interactive command line',
        }

    def load(self, argv):
        if (len(argv) != 1):
            print
            print "ptree load <ptree file dump>"
            sys.exit(-1)
        ptree = PropertyTree.load(argv[0])
        print ptree

    def interact(self, argv):
        print 'PropertyTree Interactive Command Line'
        print 'Seperator: .'
        print 'Commands:'
        print '  add    -- add a key value pair'
        print '  remove -- remove a key'
        print '  get    -- get the value of a pattern'
        print '  print  -- print the current tree'
        print '  dump   -- dump the tree to a file'
        print '  load   -- load a tree from file'
        print '  exit   -- exit'
        ptree = PropertyTree()
        while(True):
            next = raw_input('>>')
            try:
                args = next.split(' ')
                if args[0] == 'add':
                    ptree.add(args[1].strip(), eval(args[2]))
                elif args[0] == 'remove':
                    ptree.remove(args[1].strip())
                elif args[0] == 'get':
                    if len(args) == 2:
                        print ptree.getv(args[1].strip())
                    else:
                        print ptree.getv(args[1].strip(), True)
                elif args[0] == 'print':
                    print ptree
                elif args[0] == 'dump':
                    PropertyTree.dump(ptree, args[1].strip())
                elif args[0] == 'load':
                    ptree = PropertyTree.load(args[1].strip())
                elif args[0] == 'exit':
                    break
                else:
                    print 'unknown command'
            except:
                traceback.print_exc(file=sys.stdout)

def main():
    testPropertyTree()

if __name__ == '__main__':
    main()


            

