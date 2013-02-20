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
    REGEX_FILTER_PATTERN_KEY = "regex.filter.pattern"
    def __init__(self, conf):
        pattern = conf.get(REGEX_FILTER_PATTERN_KEY)
        if (pattern == None):
            pattern = ""
        self.regex = re.compile(pattern)

    def accept(self, string):
        return self.regex.search(string) != None
