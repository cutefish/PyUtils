import logging
import os
import shutil
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
        except Exception as e:
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

    def set_proxy(self, proxy):
        if proxy['http'] is not None:
            self.proxy_lines.append('ENV http_proxy {0}'.format(proxy['http']))
        if proxy['https'] is not None:
            self.proxy_lines.append('ENV https_proxy {0}'.format(proxy['https']))
        if (proxy['https'] is None) and (proxy['http'] is not None):
            self.proxy_lines.append('ENV https_proxy {0}'.format(proxy['http']))
        if proxy['http'] is not None:
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
            writer.writelines(lines)

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
        with open('{0}/{1}'.format(self.get_tmpdir(),
                                   self.startup_script),
                  'w') as writer:
            writer.writelines(self.startup_script_lines)

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
        self.range_regex = ''
        self.range_vals = ['']
        self.image = None
        self.name_pattern = None
        self.volumes = []
        self.envs = []
        self.ip_addresses = []
        self.mac_addresses = []
        self.dns_address = None

    def set_range_regex(self, regex):
        self.range_regex = regex

    def set_range_vals(self, vals):
        self.range_vals = vals

    def set_image(self, image):
        self.image = image
        self.set_depnames([image])

    def set_name_pattern(self, pattern):
        self.name_pattern = pattern

    def add_volume_mapping(self, src, dst):
        self.volumes.append('{0}:{1}:ro'.format(src, dst))

    def add_env(self, name, value):
        self.envs.append('"{0}={1}"'.format(name, value))

    def run_internal(self):
        for i, val in enumerate(self.range_vals):
            name = re.sub(self.range_regex, str(val), self.name_pattern)
            tmpdir = ('{0}/containers/{1}'.
                      format(self.execution.get_tmpdir(),
                             name))
            os.makedirs(tmpdir)
            docker_run = DockerRun()
            self.log(logging.INFO, 'Starting container: {0}'.format(name))
            retcode = docker_run.detach().hostname(name).\
                add_cap('NET_ADMIN').add_cap('SYS_ADMIN').\
                mac(self.mac_addresses[i]).dns(self.dns_address).\
                volumes(self.volumes).envs(self.envs).\
                name(name).run(self.image, self.out_msgs, self.err_msgs)
            if retcode != 0:
                raise ValueError('Docker run faild: {0}'.format(name))
