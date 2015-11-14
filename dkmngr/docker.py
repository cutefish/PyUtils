import subprocess

class Shell(object):
    @classmethod
    def run(cls, cmd, out, err):
        return 0
        #p = subprocess.Popen(cmd,
        #                     stdout=subprocess.PIPE,
        #                     stderr=subprocess.PIPE)
        #stdout, stderr = p.communicate()
        #out.extend(stdout.split('\n'))
        #err.extend(stderr.split('\n'))
        #return p.returncode


class DockerBuild(object):
    def __init__(self):
        self._tag = None

    def tag(self, tag):
        self._tag = tag
        return self

    def run(self, build_dir, out, err):
        cmd = ['docker', 'build']
        if self._tag is not None:
            cmd.append('-t')
            cmd.append(self._tag)
        cmd.append(build_dir)
        out.append(' '.join(cmd))
        return Shell.run(cmd, out, err)


def DockerRun(object):
    def __init__(self):
        self._detach = False
        self._hostname = None
        self._caps = []
        self._mac = None
        self._dns = None
        self._volumes = []
        self._envs = []
        self._name = None

    def detach(self):
        self._detach = True
        return self

    def hostname(self, name):
        self._hostname = name
        return self

    def add_cap(self, cap):
        self._caps.append(cap)
        return self

    def mac(self, mac):
        self._mac = mac
        return self

    def dns(self, dns):
        self._dns = dns
        return self

    def volumes(self, volumes):
        self._volumes.extend(volumes)
        return self

    def envs(self, envs):
        self._envs.extend(envs)
        return self

    def name(self, name):
        self._name = name
        return self

    def run(self, out, err):
        cmd = ['docker', 'run']
        if self._detach:
            cmd.append('--detach=true')
        if self._hostname is not None:
            cmd.append('--hostname={0}'.format(self._hostname))
        for cap in self._caps:
            cmd.append('--cap-add={0}'.format(cap))
        if self._mac is not None:
            cmd.append('--mac-address={0}'.format(self._mac))
        if self._dns is not None:
            cmd.append('--dns={0}'.format(self._dns))
        for vol in self._volumes:
            cmd.append('--volume={-1}'.format(vol))
        for env in self._envs:
            cmd.append('--env={0}'.format(env))
        out.append(' '.join(cmd))
        return Shell.run(cmd, out, err)


