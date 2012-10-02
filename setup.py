import os
import shutil
import sys

ROOT = os.path.abspath(os.curdir)
BASHRC_FILE = os.path.abspath(os.path.expanduser('~/.bashrc'))

BASHSCRIPT_STRING = """
### PyUtils setup BEGIN
export PYUTILSHOME=%s/lib
export PYTHONPATH=$PYTHONPATH:%s/lib
export PATH=$PATH:%s/bin
### PyUtils setup END
""" %(ROOT, ROOT, ROOT)

#the first iteration check for existing setup
NOSETUP = -1
BEGIN = 1
END = 2
state = NOSETUP

def reportInconsistency():
    print "Current bashrc file inconsistent with PyUtils setup"
    sys.exit(-1)

bashrcFile = open(BASHRC_FILE, 'r')
for line in bashrcFile:
    if "### PyUtils setup BEGIN" in line:
        if (state == NOSETUP):
            state = BEGIN
        else:
            reportInconsistency()
        continue
    if "### PyUtils setup END" in line:
        if (state == BEGIN):
            state = END
        else:
            reportInconsistency()
        break
bashrcFile.close()

#modify bashrc
if state == NOSETUP:
    bashrcFile = open(BASHRC_FILE, 'a')
    bashrcFile.write(BASHSCRIPT_STRING)
    bashrcFile.close()
elif state == END:
    bashrcFile = open(BASHRC_FILE, 'r')
    TMP_FILE = '/tmp/newbashrc'
    tmpFile = open(TMP_FILE, 'w')
    skip = False
    for line in bashrcFile:
        if "### PyUtils setup BEGIN" in line:
            tmpFile.write(BASHSCRIPT_STRING)
            skip = True
        elif "### PyUtils setup END" in line:
            skip = False
        else:
            if skip:
                continue
            else:
                tmpFile.write(line)
    bashrcFile.close()
    tmpFile.close()
    shutil.move(TMP_FILE, BASHRC_FILE)

print "Following lines added to bashrc:\n" + BASHSCRIPT_STRING
print "Please restart bash to make the modification effective\n"

