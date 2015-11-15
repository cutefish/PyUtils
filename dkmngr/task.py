import logging
import os
import re
import shutil
import stat
import textwrap
import traceback

from execution import StopExecutionAction
from docker import DockerBuild, DockerRun

class Task(object):
    QUEUED, RUNNING, SUCCEEDED, FAILED = range(4)
    def __init__(self, execution):
        self.execution = execution
        self.name = None
        self.depnames = []
        self.depends = set([])
        self.fail_action = StopExecutionAction(self)
        self.logger = logging.getLogger('task')
        self.log_prefix = ''
        self.status = Task.QUEUED
        self.out_msgs = []
        self.err_msgs = []

    def set_name(self, name):
        self.name = name

    def set_tasktype(self, tasktype):
        self.tasktype = tasktype

    def set_depnames(self, depnames):
        self.depnames.extend(depnames)

    def add_depend(self, task):
        self.depends.add(task)

    def get_depends(self):
        return self.depends

    def get_name(self):
        return self.name

    def get_out_msgs(self):
        return self.out_msgs

    def get_err_msgs(self):
        return self.err_msgs

    def is_failed(self):
        return self.status == Task.FAILED

    def is_succeeded(self):
        return self.status == Task.SUCC

    def is_done(self):
        return self.status > Task.RUNNING

    def run(self):
        try:
            self.status = Task.RUNNING
            self.run_internal()
            self.status = Task.SUCCEEDED
        except:
            self.err_msgs.extend(traceback.format_exc().split('\n'))
            self.status = Task.FAILED

    def run_internal(self):
        raise NotImplementedError()

    def log(self, lvl, msg, prefix=None):
        if prefix is None:
            prefix = self.log_prefix
        self.logger.log(lvl, msg, extra={
            'log_prefix' : prefix,
        })


    def __str__(self):
        return '[{0}({1})]'.format(
            self.get_name(),
            ','.join([d.get_name() for d in self.get_depends()])
        )


class ImageBuildTask(Task):
    def __init__(self, execution):
        super(ImageBuildTask, self).__init__(execution)
        self.log_prefix = 'image'
        self.from_lines = ['FROM ubuntu:14.04']
        self.proxy_lines = []
        self.install_lines = []
        self.copy_files = []
        self.volume_lines = []
        self.startup_dir = '/startup/'
        self.startup_script = 'dkimg_startup.sh'
        self.startup_script_lines = []
        self.mkdir_lines = ['RUN mkdir {0}'.format(self.startup_dir)]
        self.copy_lines = []
        self.startup_lines = []
        self.set_proxy(self.execution.get_proxy())

    def set_proxy(self, proxy):
        if proxy.get('http') is not None:
            self.proxy_lines.append('ENV http_proxy {0}'.format(proxy['http']))
        if proxy.get('https') is not None:
            self.proxy_lines.append('ENV https_proxy {0}'.format(proxy['https']))
        if (proxy.get('https') is None) and (proxy.get('http') is not None):
            self.proxy_lines.append('ENV https_proxy {0}'.format(proxy['http']))
        if proxy.get('http') is not None:
            self.proxy_lines.append(
                'RUN echo "Acquire::http::Proxy \"{0}\";" > /etc/apt/apt.conf'.
                format(proxy['http']))

    def set_install(self, packages):
        self.install_lines.append(
            'RUN apt-get update && apt-get install -y {0}'.
            format(' '.join(packages)))

    def set_startup_scripts(self, scripts):
        self.startup_script_lines.append('#!/bin/bash')
        for script in scripts:
            self.startup_script_lines.append(
                '{0}/{1}'. format(self.startup_dir, script))
        self.startup_script_lines.append('sleep {0}'.format(24 * 3600))
        self.startup_lines.append(
            'ENTRYPOINT ["sh", "{0}{1}"]'. format(self.startup_dir,
                                                  self.startup_script))
        self.copy_lines.append('COPY {0} {1}'.
                               format(self.startup_script,
                                      self.startup_dir))

    def copy_to_startupdir(self, paths):
        for path in paths:
            self.copy_files.append(path)
            self.copy_lines.append('COPY {0} {1}'.
                                   format(os.path.basename(path.rstrip('/')),
                                          self.startup_dir))

    def set_volumes(self, paths):
        self.volume_lines = ['VOLUME {0}'.format(' '.join(paths))]
        for path in paths:
            path = path.rstrip('/')
            self.mkdir_lines = ['RUN mkdir -p {0}'.format(os.path.dirname(path))]

    def copy(self, src, dst):
        if not os.path.exists(src):
            raise OSError('Path does not exist: {0}'.format(src))
        self.mkdir_lines.append('RUN mkdir -p {0}'.format(dst))
        self.copy_files.append(src)
        path = os.path.basename(src.rstrip('/'))
        self.copy_lines.append('COPY {0} {1}'.format(path, dst))

    def get_tmpdir(self):
        return '{0}/image/{1}'.format(self.execution.get_tmpdir(),
                                      self.get_name())

    def run_internal(self):
        os.makedirs(self.get_tmpdir())
        self.generate_dockerfile()
        self.gather_image_files()
        self.generate_startup_file()
        self.build_image()

    def generate_dockerfile(self):
        self.log(logging.INFO, 'Generate docker file.')
        lines = self.get_dockerfile_lines()
        with open('{0}/Dockerfile'.format(self.get_tmpdir()), 'w') as writer:
            for line in lines:
                writer.write(line + '\n')

    def get_dockerfile_lines(self):
        lines = []
        lines.extend(self.from_lines)
        lines.extend(self.proxy_lines)
        lines.extend(self.install_lines)
        lines.extend(self.mkdir_lines)
        lines.extend(self.volume_lines)
        lines.extend(self.copy_lines)
        lines.extend(self.startup_lines)
        return lines

    def gather_image_files(self):
        self.log(logging.INFO, 'Gather image files.')
        for path in self.copy_files:
            shutil.copy(path, self.get_tmpdir())

    def generate_startup_file(self):
        self.log(logging.INFO, 'Generate startup script.')
        startup_file = '{0}/{1}'.format(self.get_tmpdir(),
                                        self.startup_script)
        with open(startup_file, 'w') as writer:
            for line in self.startup_script_lines:
                writer.write(line + '\n')
        st = os.stat(startup_file)
        os.chmod(startup_file, st.st_mode | stat.S_IEXEC)

    def build_image(self):
        self.log(logging.INFO, 'Build image.')
        docker_build = DockerBuild()
        docker_build.tag(self.get_name())
        retcode = docker_build.run(self.get_tmpdir(),
                                   self.out_msgs,
                                   self.err_msgs)
        if retcode != 0:
            raise ValueError('Docker build faild: {0}'.
                             format(self.get_tmpdir()))


class ContainersRunTask(Task):
    def __init__(self, execution):
        super(ContainersRunTask, self).__init__(execution)
        self.log_prefix = 'containers'
        self.ids = None
        self.sub_regex = ''
        self.image = None
        self.ctn_names = []
        self.volumes = []
        self.envs = []
        self.ip_addresses = []
        self.mac_addresses = []
        self.dns_address = None

    def set_image(self, image):
        self.image = image
        self.set_depnames([image])

    def set_ids(self, vals):
        self.ids = vals
        names = []
        for val in self.ids:
            name = '{0}-{1}'.format(self.name, val)
            names.append(name)
        self.ctn_names = names

    def set_sub_regex(self, var):
        self.sub_regex = '\${0}'.format(var)

    def set_name_pattern(self, pattern):
        names = set([])
        for val in self.ids:
            name = re.sub(self.sub_regex, str(val), pattern)
            names.add(name)
        if len(names) != len(self.ids):
            raise ValueError('Pattern cannot match ids after replacement.'
                             'ids={0} pattern={1} names={2}'.
                             format(self.ids, pattern, names))
        self.ctn_names = sorted(names)

    def add_volume_mapping(self, src, dst):
        if not os.path.isdir(src):
            raise OSError('Cannot find directory: {0}'.format(src))
        self.volumes.append('{0}:{1}:ro'.format(src, dst))

    def add_env(self, name, value):
        self.envs.append('"{0}={1}"'.format(name, value))

    def set_ip_addresses(self, ips):
        self.ip_addresses = ips
        self.set_mac_addresses()

    def set_mac_addresses(self):
        mac_addresses = []
        for ip in self.ip_addresses:
            parts = ip.split('.')
            parts = map(lambda x : x.zfill(3), parts)
            chars = ''.join(parts)
            parts = textwrap.wrap(chars)
            mac = ':'.join(parts)
            mac_addresses.append(mac)
        self.mac_addresses = mac_addresses

    def get_num_containers(self):
        return len(self.ids)

    def get_container_names(self):
        return self.ctn_names

    def run_internal(self):
        for i, val in enumerate(self.ids):
            name = self.ctn_names[i]
            tmpdir = ('{0}/containers/{1}'.
                      format(self.execution.get_tmpdir(),
                             name))
            os.makedirs(tmpdir)
            docker_run = DockerRun()
            self.log(logging.INFO, 'Starting container: {0}'.format(name))
            docker_run.detach().hostname(name).\
                add_cap('NET_ADMIN').add_cap('SYS_ADMIN').\
                dns(self.dns_address).\
                volumes(self.sublst(self.volumes, val)).\
                envs(self.sublst(self.envs, val)).\
                name(name)
            if len(self.mac_addresses) != 0:
                docker_run.mac(self.mac_addresses[i])
            retcode = docker_run.run(self.image, self.out_msgs, self.err_msgs)
            if retcode != 0:
                raise ValueError('Docker run faild: {0}'.format(name))

    def sublst(self, lst, val):
        result = []
        for e in lst:
            result.append(re.sub(self.sub_regex, str(val), e))
        return result


class DnsImageBuildTask(ImageBuildTask):
    def __init__(self, execution, mapping):
        super(ImageBuildTask, self).__init__(execution)
        self.mapping = mapping
        self.set_install(['bind9 host'])
