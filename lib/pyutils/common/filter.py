"""
common.filter

Filters

"""
import re

class Filter:
    def __init__(self):
        pass

    def accept(self):
        return True

class RegexFilter:
    def __init__(self, pattern):
        self.regex = re.compile(pattern)

    def accept(self, string):
        return self.regex.search(string) != None
