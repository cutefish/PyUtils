import imp

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
