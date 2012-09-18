"""
Get Module Information.
"""

import inspect
import re

def searchMembers(objInst, pattern):
    members = inspect.getmembers(objInst)
    ret = []
    patternRe = re.compile(pattern)
    for m in members:
        name, value = m
        if re.search(patternRe, name) != None:
            ret.append(m)
        if (isinstance(value, str)) and (re.search(patternRe, value) != None):
            ret.append(m)
    return ret

