"""
system.filesystem

filesystem utilities.

"""

import subprocess

class Volume(object):
    def __init__(self, fs, nkblocks, used, available, use, mounton):
        self._fs = str(fs)
        self._nkblocks = int(nkblocks)
        self._used = int(used)
        self._available = int(available)
        self._use = float(use.strip().strip('%')) / 100.0
        self._mounton = str(mounton)

    @property
    def fs(self):
        return self._fs

    @property
    def nkblocks(self):
        return self._nkblocks

    @property
    def used(self):
        return self._used

    @property
    def available(self):
        return self._available

    @property
    def use(self):
        return self._use

    @property
    def mounton(self):
        return self._mounton

    def __iter__(self):
        yield self._fs
        yield self._nkblocks
        yield self._used
        yield self._available
        yield self._use
        yield self._mounton

    def __str__(self):
        return '%s %s %s %s %s%% %s' %(
            self._fs,
            self._nkblocks,
            self._used,
            self._available,
            int(self._use * 100),
            self._mounton)


class Volumes(object):
    def __init__(self):
        self.volumes = {}

    def df(self):
        p = subprocess.Popen(["df"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stderr != None and stderr != '':
            raise IOError("Linux command df error: " + stderr)
        results = stdout.strip('\n').split('\n')
        for line in results[1:]:
            fs, nkblocks, used, available, use, mounton = line.split()
            volume = Volume(fs, nkblocks, used, available, use, mounton)
            self.volumes[mounton] = volume

    def __iter__(self):
        for k, v in self.volumes.iteritems():
            yield k, v

    def __str__(self):
        """Pretty print the volumes."""
        fsWidth = 15
        nkblocksWidth = 15
        usedWidth = 15
        availableWidth = 15
        useWidth = 5
        for v in self.volumes.values():
            if len(v.fs) > fsWidth:
                fsWidth = len(v.fs)
        string = ''
        for v in self.volumes.values():
            fs, nkblocks, used, available, use, mounton = v
            string += fs.ljust(fsWidth)
            string += str(nkblocks).rjust(nkblocksWidth)
            string += str(used).rjust(usedWidth)
            string += str(available).rjust(availableWidth)
            string += str(int(use * 100)).rjust(useWidth)
            string += '% '
            string += mounton
            string += '\n'
        return string

def main():
    volumes = Volumes()
    volumes.df()
    print volumes

if __name__ == '__main__':
    main()
