"""
PyUtils.Path

Path object.

"""

import glob
import os
import shutil

class Path:
    def __init__(self, path):
        if isinstance(path, str):
            self.name = os.path.abspath(os.path.expanduser(path))
            return
        if isinstance(path, Path):
            self.name = path.name
            return

    def isFile(self):
        """Return if self is a file."""
        return os.path.isfile(self.name)

    def isDir(self):
        """Return if self is a directory."""
        return os.path.isdir(self.name)

    def baseName(self):
        """Return base name."""
        return os.path.basename(self.name)

    def parent(self):
        """Return parent Path object."""
        return os.path.dirname(self.name)

    def ls(self, pattern="*"):
        """Return child Path objects. Similar to linux ls utility"""
        pathList = []
        for p in glob.iglob(pattern):
            pathList.append(Path(p))
        return pathList

    def open(self, mode='r', buffering=1):
        """Return the file handler. A simple wrapper for built-in open()."""
        f = open(self.name, mode, buffering)
        return f

    def __repr__(self):
        return self.name

    @staticmethod
    def isFileOrDie(name):
        """Raise exception if @name not a file or die."""
        if not Path(name).isFile():
            raise IOError("%s is not a file" % name)

    @staticmethod
    def isDirOrDie(name):
        """Raise exception if @name not a directory or die."""
        if not Path(name).isDir():
            raise IOError("%s is not a directory" % name)

    @staticmethod
    def move(src, dst):
        """Move src to dst."""
        inPath = Path(src)
        outPath = Path(dst)
        shutil.move(inPath.name, outPath.name)

def main():
    path = Path("~/t")
    print path.isFile()
    path = Path("~/t1")
    print path.isFile()
    path = Path("~/Documents")
    print path.isDir()
    print path.parent()
    print path.ls()
    try:
        Path.isFileOrDie("~/Doc")
    except Exception as e:
        print e

if __name__ == '__main__':
    main()
