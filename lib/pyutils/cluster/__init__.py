
modules = {
    "broadcast" : "Broadcast commands",
}

def printUsage():
    print ("available modules:\n>>" +
           "\t\n".join(key + ": " + modules[key] for key in modules))



