import imp
import inspect

import clirunnable as clir

def loadPkgModule(name, package):
    """
    Recursively import until load the module within a package.

    @name is separted by ., e.g. foo.bar
    @topLevel is the top level package.

    @return the module
    """
    hierarchy = name.split('.')
    currLevel = package
    importedName = package.__name__
    for moduleName in hierarchy:
        try:
            importedName = importedName + '.' + moduleName
            f, p, d = imp.find_module(moduleName, currLevel.__path__)
            currLevel = imp.load_module(moduleName, f, p, d)
        except ImportError as ie:
            raise ImportError(importedName, ie)
    return currLevel

def loadFileModule(name, path=None):
    """
    Load a module from file.

    @name is the name of the module.
    @path is the search path of the module.
    """
    if path != None and not isinstance(path, list):
        path = [path]
    try:
        f, p, d = imp.find_module(name, path)
        return impl.load_module(name, f, p, d)
    except ImportError as ie:
        raise ImportError(ie)

def getSubClass(module, base):
    """
    Search in the module and find the first class of inherits from a base class.

    @module is the module.
    @base is the base class.

    @return the class object.
    """
    members = inspect.getmembers(module)
    for name, obj in members:
        if (inspect.isclass(obj)):
            if issubclass(obj, base):
                return obj
    return None

def getClass(module, name):
    """
    Search in the module for a class with certain name.

    @module is the module
    @name is the class name

    @return the class
    """
    members = inspect.getmembers(module)
    for key, obj in members:
        if (inspect.isclass(obj)):
            if key == name:
                return obj
    return None

def newInstance(module, name, conf, defaultCls=None):
    cls = getClass(module, name)
    if cls == None:
        cls = defaultCls
    if cls == None:
        return None
    return cls(conf)

