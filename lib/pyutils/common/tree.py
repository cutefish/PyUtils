"""
tree.py

Tree Data Structures.
"""

import pickle
import re

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
        self.charRe = '[a-zA-Z0-9-_]'
        self.validRe = re.compile('^(\%s?%s+)+$'%(self.sep, self.charRe))

    def normalizeKey(self, key):
        if not self.validRe.match(key):
            raise KeyError("Bad key: " + key)
        if not key.startswith(self.sep):
            return self.sep + key

    def splitKey(self, key):
        """ Split key into parent and child. """
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

    def _dive(self, key, node=None, create=False):
        levelKeys = key.split(self.sep)
        curr = node
        if curr == None:
            curr = self.root
        currKey = ""
        for i in range(len(levelKeys)):
            if i == 0:
                continue
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
        return self._dive(key)

    def add(self, key, val, overwrite=True):
        """ Add the TreeNode matching the key.  

        Return the added TreeNode.
        If key exists and overwrite is False, raise KeyError.
        
        """
        key = self.normalizeKey(key)
        parentKey, childKey = self.splitKey(key)
        parent = self._dive(parentKey, create=True)
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
            parent = self._dive(parentKey, create=False)
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
                ret.append((curr, fullKey.lstrip(self.sep)))
            for child in curr.children:
                queue.append((child, fullKey + self.sep + child.key))
        return ret

    def match(self, pattern):
        """ Search for all leaf nodes matching the wildcard pattern."""
        #check validity of the pattern
        lvlp = '[a-zA-Z0-9-_]+'
        sep = self.sep
        # normalize: remove repeated * and check validity
        pattern = re.sub('(\*\.)+','*.', pattern)
        legal = re.compile('^\%s?((\*\%s)|(%s\%s))*(\*|%s)$' %(
            sep, sep, lvlp, sep, lvlp))
        if not legal.match(pattern):
            raise KeyError("Bad pattern: " + pattern)
        if not pattern.startswith(self.sep):
            pattern = self.sep + pattern
        #group keys
        levelKeys = pattern.split(self.sep)
        keys = []
        prevstop = 0
        for i in range(len(levelKeys)):
            if (levelKeys[i] == '*'):
                prev = self.sep.join(levelKeys[prevstop:i])
                keys.append(prev)
                keys.append('*')
                prevstop = i + 1
            if i == len(levelKeys) - 1 and prevstop <= i:
                prev = self.sep.join(levelKeys[prevstop:i])
                keys.append(prev)
        #foreach key, if its a wildcard, then search, otherwise, dive
        queue = []
        leaves = []
        try:
            first = self._dive(keys[0], create=False)
        except KeyError:
            return leaves
        queue.append((first, keys[0], 1))
        while len(queue) != 0:
            curr, fullKey, index = queue.pop()
            if index == len(keys):
                #if we exhaust the matching pattern, any descendants match
                if not curr.hasChild():
                    leaves.append((curr, fullKey))
                    continue
                for next in curr.children:
                    fullKey = fullKey + self.sep + next.key
                    queue.append((next, fullKey, index))
                continue
            nextKey = keys[index]
            if (nextKey != '*'):
                #nextKey is not *, directly find the next node
                try:
                    next = self._dive(nextKey, curr, create=False)
                    fullKey = fullKey + self.sep + nextKey
                    index = index + 1
                    queue.append((next, fullKey, index))
                except KeyError:
                    #key not found, this path is dead
                    pass
            else:
                #nextKey is *, find the descendant parents matching the first
                index = index + 1
                if index == len(keys):
                    queue.append((curr, fullKey, index))
                    continue
                firstKey = keys[index].split(self.sep)[0]
                for next, key in self._dfsKey(firstKey, curr):
                    key = key.rstrip(self.sep + firstKey)
                    queue.append(
                        (next, fullKey +self.sep + key, index))
        return leaves

    def getv(self, key):
        if not '*' in key:
            try:
                node = self.find(key)
                return node.val
            except KeyError:
                return None
        else:
            keyvals = {}
            for node, key in self.match(key):
                keyvals[key.lstrip(self.sep)] = node.val
            return keyvals

    def setv(self, key, val):
        self.add(key, val, True)

    @staticmethod
    def dump(tree, fd):
        pickle.dump(tree, fd)

    @staticmethod
    def load(fd):
        tree = pickle.load(fd)
        return tree

    def __str__(self):
        """Retrun all the keys and values."""
        queue=[]
        queue.append((self.root, self.root.key))
        ret = []
        while len(queue) != 0:
            curr, fullKey = queue.pop()
            if not curr.hasChild():
                ret.append(fullKey + ": " + str(curr.val))
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
    print pt.getv("plan0.iter0.job0.mapper.0.*")
    print pt.getv("plan0.iter0.job0.mapper.*.exec.time")
    print pt.getv("*.mapper.*.read.type")
    print
    fd = open('/tmp/testpt', 'w')
    PropertyTree.dump(pt, fd)
    fd.close()
    fd = open('/tmp/testpt', 'r')
    pt = PropertyTree.load(fd)
    fd.close()
    print pt
    print pt.getv("plan0.iter0.job0.mapper.0.*")
    print pt.getv("plan0.iter0.job0.mapper.*.exec.time")
    print pt.getv("*.mapper.*.read.type")
    fd.close()

def main():
    testPropertyTree()

if __name__ == '__main__':
    main()


            

