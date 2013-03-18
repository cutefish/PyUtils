"""
tree.py

Tree Data Structures.
"""

import re

class PropertyTreeNode(object):
    """ Property tree node. """
    def __init__(self, key, val, children=[]):
        self._key = key
        self._val = val
        self._children = children

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
        self.root = PropertyTreeNode("", None)
        self.sep = sep
        self.invKeyRe = re.compile('[^a-zA-Z0-9-_%s]'%self.sep)

    def _dive(self, key, create=False):
        checkKeyValidity(key)
        levelKeys = key.split(self.sep)
        curr = self.root
        currKey = ""
        for i in range(len(levelKeys)):
            next = None
            levelKey = levelKeys[i]
            currKey = currKey + self.sep + levelKeys[i]
            for child in curr.children:
                if child.key == currKey:
                    next = child
                    break
            if next == None:
                if not create:
                    raise KeyError("Key not found: " + currKey)
                else:
                    next = PropertyTreeNode(currKey, None)
                    curr.children.add(next)
            curr = next
        return curr

    def find(self, key):
        """ Find the PropertyTreeNode according to the key.

        If the keys in each level is regular: [a-zA-Z0-9-_]* Return the node if
        found. Otherwise throw KeyError.

        If the keys contains wildcard charactor '*', returns the set of nodes
        matches the wildcard.

        """
        if not key.contains('*'):
            return self._dive(key)

    def add(self, key, val, overwrite=True):
        """ Add the PropertyTreeNode according to the key.  

        Return the added PropertyTreeNode.
        If key exists and overwrite is False, raise KeyError.
        
        """
        parentKey = getParentKey(self, key)
        parent = self._dive(parentKey, create=True)
        curr = None
        for child in parent.children:
            if child.key == key:
                if not overwrite:
                    raise KeyError("Key already exists: " + key)
                curr = child
        if curr == None:
            curr = PropertyTreeNode(key, val)
            parent.children.add(curr)
        else:
            curr.val = val
        return curr

    def remove(self, key):
        """ Remove the PropertyTreeNode according to the key. 

        Return True if existed. False otherwise.
        
        """
        parentKey = getParentKey(self, key)
        try:
            parent = self._dive(parentKey, create=False)
        except KeyError:
            return False
        for child in parent.children:
            if child.key == key:
                parent.children.remove(child)
                return True
        return False

    def getParentKey(self, key):
        return re.sub('\%s[a-zA-Z0-9-_]*$'%self.sep, '', key)

    def getCommonKey(self, key1, key2):
        levelKeys1 = key1.split(self.sep)
        levelKeys2 = key2.split(self.sep)
        minLevel = min(len(levelKeys1), len(levelKeys2))
        common = []
        for i in range(minLevel):
            if (levelKeys1[i] != levelKeys2[i]):
                return common
            common.append(levelKeys1[i])

    def checkKeyValidity(self, key):
        if self.invKeyRe.search(key):
            raise KeyError("Bad key: " + key)

    def findKeys(self, keys):

