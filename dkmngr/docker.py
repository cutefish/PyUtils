import subprocess


class DockerBuild(object):
    def __init__(self):
        self.tag = None

    def tag(self, tag):
        self.tag = tag
        return self

    def run(self, build_dir):
        cmd = []
        if self.tag is not None:
            cmd.append('-t')
            cmd.append(self.tag)
        cmd.append(build_dir)
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode
