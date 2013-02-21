import imp
import inspect
import sys

def loadModule(name, path=[]):
    """
    Load a module according to the name heirarchy.

    @name is separted by '.', e.g. foo.bar.
    @path is the additional path to search.

    @return the module
    @raise ImportError. Currently successfully imported name and the module can
    be accessed through its first and second argument.

    """
    hierarchy = name.split('.')
    if not isinstance(path, list):
        path = [path]
    path += sys.path
    currLevel = None
    importedName = ""
    for moduleName in hierarchy:
        try:
            try:
                currPath = currLevel.__path__
            except:
                currPath = path
            f, p, d = imp.find_module(moduleName, currPath)
            currLevel = imp.load_module(moduleName, f, p, d)
            if importedName != "":
                importedName = importedName + '.' + moduleName
            else:
                importedName = moduleName
        except ImportError as ie:
            raise ImportError(importedName, currLevel, moduleName, ie)
    return currLevel

def loadClass(name, path=[], interface=None):
    """
    Search for a class.

    @name is the name of the class, with the same convention as @loadModule()
    @interface is the interface class type for @return 

    @return the class object or None if error
    """
    success = False
    try:
        m = loadModule(name, path)
        success = True
    except ImportError as ie:
        lname, m, n, e = ie.args
    #if successfully load a module, we need to search for a class inherited
    #from @interface in that module
    if success:
        if interface == None:
            raise ImportError("%s is a module, not a class" %name)
        members = inspect.getmembers(m)
        for clsName, cls in members:
            if (inspect.isclass(cls)):
                if issubclass(cls, interface) and not cls is interface:
                    return cls
        return None
    #load module is not fully successful, pick up from what's left
    hierarchy = name.split('.')
    loaded = lname.split('.')
    for l in loaded:
        hierarchy.pop(0)
    #search for class
    curr = m
    while True:
        currName = hierarchy.pop(0)
        members = inspect.getmembers(curr)
        for clsName, cls in members:
            if clsName == currName:
                if len(hierarchy) != 0:
                    curr = cls
                    continue
                #last level
                if inspect.isclass(cls):
                    if (interface != None) and (not issubclass(cls, interface)):
                        raise ImportError("Class not found: " + name)
                    return cls
                else:
                    raise ImportError("Class not found: " + name)
    raise ImportError("Class not found: " + name)

