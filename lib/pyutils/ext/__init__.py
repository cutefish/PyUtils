modules = {
    "ec2" : "Amazon EC2 utilities",
}

def printUsage():
    print ("available modules:\n>>" +
           "\t\n".join(key + ": " + modules[key] for key in modules))



