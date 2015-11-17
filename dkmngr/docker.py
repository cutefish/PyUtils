import re
import shlex
import subprocess

class Shell(object):
    @classmethod
    def run(cls, cmd, out, err):
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stdout != '':
            out.extend(stdout.split('\n'))
        if stderr != '':
            err.extend(stderr.split('\n'))
        return p.returncode


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


class DockerRun(object):
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

    def run(self, image, out, err):
        self.cleanup_exist()
        cmd = ['docker', 'run']
        if self._detach:
            cmd.append('--detach=true')
        if self._hostname is not None:
            cmd.append('--hostname={0}'.format(self._hostname))
        if self._name is not None:
            cmd.append('--name={0}'.format(self._name))
        for cap in self._caps:
            cmd.append('--cap-add={0}'.format(cap))
        if self._mac is not None:
            cmd.append('--mac-address={0}'.format(self._mac))
        if self._dns is not None:
            cmd.append('--dns={0}'.format(self._dns))
        for vol in self._volumes:
            cmd.append('--volume={0}'.format(vol))
        for env in self._envs:
            cmd.append('--env={0}'.format(env))
        cmd.append(image)
        out.append(' '.join(cmd))
        return Shell.run(cmd, out, err)

    def cleanup_exist(self):
        out = []
        err = []
        Shell.run(['docker', 'kill', self._name], out, err)
        Shell.run(['docker', 'rm', self._name], out, err)

    def logs(self, out_dir):
        cmd = ['docker', 'logs']
        cmd.append(self._name)
        out = []
        err = []
        Shell.run(cmd, out, err)
        out_file = '{0}/log.out'.format(out_dir)
        err_file = '{0}/log.err'.format(out_dir)
        with open(out_file, 'w') as writer:
            for line in out:
                writer.write(line + '\n')
        with open(err_file, 'w') as writer:
            for line in err:
                writer.write(line + '\n')


class DockerExec(object):
    def __init__(self, name):
        self.container_name = name

    def run(self, cmd, out, err):
        docker_cmd = ['docker', 'exec']
        docker_cmd.append(self.container_name)
        docker_cmd.extend(shlex.split(cmd))
        Shell.run(docker_cmd, out, err)


class IPLocator(object):
    def __init__(self):
        self.docker0 = self.get_docker0_ip()
        self.prefix = '.'.join(self.docker0.split('.')[0:2])
        self.counter = [0, 1]

    def get_docker0_ip(self):
        output = subprocess.check_output(['ifconfig'])
        lines = output.split('\n')
        result = None
        for i, line in enumerate(lines):
            if line.startswith('docker0'):
                inet_line= lines[i + 1]
                regex = re.compile(
                    'inet addr:(?P<ip>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)')
                result = regex.search(inet_line).group('ip')
                break
        if result is None:
            raise OSError('Cannot find docker interface.')
        return result

    def next_ip(self):
        curr = '.'.join([self.prefix,
                         str(self.counter[0]),
                         str(self.counter[1])])
        self.inc_counter()
        if curr == self.docker0:
            return self.next_ip()
        return curr

    def inc_counter(self):
        self.counter[1] += 1
        if self.counter[1] == 256:
            self.counter[1] = 0
            self.counter[0] += 1
        if self.counter[0] == 256:
            raise ValueError('All IP used up.')
