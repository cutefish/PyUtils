import imp
import inspect

import CliRunnable as clir

def importModule(name, topLevel):
    """
    Recursively import until load the module.
    """
    hierarchy = name.split('.')
    currLevel = topLevel
    importedName = topLevel.__name__
    for moduleName in hierarchy:
        try:
            importedName = importedName + '.' + moduleName
            f, p, d = imp.find_module(moduleName, currLevel.__path__)
            currLevel = imp.load_module(moduleName, f, p, d)
        except ImportError:
            raise ImportError(importedName)
    return currLevel

def getRunnableClass(module):
    members = inspect.getmembers(module,
                                 lambda m : issubclass(m, clir.CliRunnable))
    if len(members) == 0:
        return None
    key, value = members.popitem();
    return value
