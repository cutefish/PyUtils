
modules = {
    "basic" : "Calculate and print count, sum , mean, std, min, max",
}

def printUsage():
    print ("available modules:\n>>" +
           "\t\n".join(key + ": " + modules[key] for key in modules))


