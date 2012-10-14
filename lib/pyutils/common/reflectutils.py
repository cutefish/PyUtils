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
        except ImportError as ie:
            raise ImportError(importedName, ie)
    return currLevel

def getRunnableClass(module):
    members = inspect.getmembers(module)
    for name, obj in members:
        if (inspect.isclass(obj)):
            if issubclass(obj, clir.CliRunnable):
                return obj
    return None
