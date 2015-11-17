import logging
import os
import re
import shutil
import stat
import textwrap
import time
import traceback

from execution import StopExecutionAction
from docker import DockerBuild, DockerRun, DockerExec
from utils import get_pretty_lines

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
            self.proxy_lines.append(
                'ENV http_proxy http://{0}'.format(proxy['http']))
        if proxy.get('https') is not None:
            self.proxy_lines.append(
                'ENV https_proxy https://{0}'.format(proxy['https']))
        if (proxy.get('https') is None) and (proxy.get('http') is not None):
            self.proxy_lines.append(
                'ENV https_proxy https://{0}'.format(proxy['http']))
        if proxy.get('http') is not None:
            self.proxy_lines.append(
                ('RUN echo "Acquire::http::Proxy \\"http://{0}\\";" '
                 '> /etc/apt/apt.conf').
                format(proxy['http']))

    def set_install(self, packages):
        self.install_lines.append(
            'RUN apt-get update && apt-get install -y {0}'.
            format(' '.join(packages)))

    def set_startup_scripts(self, scripts):
        self.startup_script_lines.append('#!/bin/bash')
        for script in scripts:
            self.startup_script_lines.append(
                '{0}{1}'. format(self.startup_dir, script))
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
        self.copy_lines.append('COPY {0} {1}/'.format(path, dst.rstrip('/')))

    def get_tmpdir(self):
        return '{0}/image/{1}'.format(self.execution.get_tmpdir(),
                                      self.get_name())

    def get_image_name(self):
        return '{0}/{1}'.format(self.execution.get_name(), self.get_name())

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
        docker_build.tag(self.get_image_name())
        retcode = docker_build.run(self.get_tmpdir(),
                                   self.out_msgs,
                                   self.err_msgs)
        if retcode != 0:
            raise ValueError('Docker build faild: {0}'.
                             format(self.get_tmpdir()))


class DnsImageBuildTask(ImageBuildTask):
    def __init__(self, execution, mapping):
        super(DnsImageBuildTask, self).__init__(execution)
        self.mapping = mapping
        self.dns_setup_file = 'dns_setup.sh'
        self.ip_config_file = 'ipconfig.py'
        self.set_name('dns-image')

    def run_internal(self):
        os.makedirs(self.get_tmpdir())
        self.set_install(['python2.7', 'dnsmasq', 'host'])
        self.set_startup_scripts([self.ip_config_file,
                                  self.dns_setup_file])
        self.copy_to_startupdir(['{0}/example/scripts/{1}'.
                                 format(self.execution.code_dir,
                                        self.ip_config_file)])
        self.copy_lines.append('COPY {0} {1}'.
                               format(self.dns_setup_file,
                                      self.startup_dir))
        self.generate_dns_setup()
        self.gather_image_files()
        self.generate_dockerfile()
        self.generate_startup_file()
        self.build_image()

    def generate_dns_setup(self):
        dns_file = '{0}/{1}'.format(self.get_tmpdir(), self.dns_setup_file)
        with open(dns_file, 'w') as writer:
            writer.write('#!/bin/bash\n')
            for hostname, ipaddr in self.mapping.iteritems():
                if 'dns' in hostname:
                    continue
                writer.write('echo "{0}\t{1}" >> /etc/hosts\n'.
                             format(ipaddr, hostname))
            writer.write('cat /etc/hosts\n')
            writer.write('service dnsmasq restart\n')
        st = os.stat(dns_file)
        os.chmod(dns_file, st.st_mode | stat.S_IEXEC)


class ContainersRunTask(Task):
    def __init__(self, execution):
        super(ContainersRunTask, self).__init__(execution)
        self.log_prefix = 'containers'
        self.ids = None
        self.wait = 0
        self.sub_regex = '\${id}'
        self.image = None
        self.ctn_names = []
        self.volumes = []
        self.envs = []
        self.ip_addresses = []
        self.mac_addresses = []
        self.dns_address = None

    def set_image(self, image):
        image_task = self.execution.get_task(image)
        self.image = image_task.get_image_name()
        self.set_depnames([image])

    def set_ids(self, vals):
        self.ids = vals
        names = []
        for val in self.ids:
            name = '{0}-{1}'.format(self.get_name(), val)
            names.append(name)
        self.ctn_names = names

    def set_wait(self, val):
        self.wait = val

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

    def set_dns(self, dns):
        self.dns_address = dns

    def add_volume_mapping(self, src, dst):
        if not os.path.isdir(src):
            raise OSError('Cannot find directory: {0}'.format(src))
        self.volumes.append('{0}:{1}:ro'.format(src, dst))

    def add_env(self, name, value):
        self.envs.append('"{0}={1}"'.format(name, value))

    def set_ip_addresses(self, ips):
        self.ip_addresses = list(ips)
        self.set_mac_addresses()

    def set_mac_addresses(self):
        mac_addresses = []
        for ip in self.ip_addresses:
            parts = ip.split('.')
            parts = map(lambda x : x.zfill(3), parts)
            chars = ''.join(parts)
            parts = textwrap.wrap(chars, 2)
            parts[0], parts[1] = ['00', '22']
            mac = ':'.join(parts)
            mac_addresses.append(mac)
        self.mac_addresses = mac_addresses

    def get_num_containers(self):
        return len(self.ids)

    def get_container_names(self):
        return self.ctn_names

    def run_internal(self):
        runs = []
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
            if len(self.ip_addresses) != 0:
                docker_run.envs(['"{0}={1}"'.
                                 format('host.desired.ip.address',
                                        self.ip_addresses[i])])
            if len(self.mac_addresses) != 0:
                docker_run.mac(self.mac_addresses[i])
            retcode = docker_run.run(self.image, self.out_msgs, self.err_msgs)
            runs.append((docker_run, tmpdir))
            if retcode != 0:
                raise ValueError('Docker run faild: {0}'.format(name))
        time.sleep(self.wait)
        for run, tmpdir in runs:
            run.logs(tmpdir)

    def sublst(self, lst, val):
        result = []
        for e in lst:
            result.append(re.sub(self.sub_regex, str(val), e))
        return result


class ContainersCmdTask(Task):
    def __init__(self, execution):
        super(ContainersCmdTask, self).__init__(execution)
        self.log_prefix = 'containers'
        self.containers_name = None
        self.containers = None
        self.ids = None
        self.sub_regex = '\${id}'
        self.commands = []
        self.expects = []

    def set_containers(self, containers_name):
        self.containers_name = containers_name
        self.set_depnames([containers_name])
        self.containers = self.execution.get_task(containers_name)
        if self.containers is None:
            raise ValueError('Cannot get containers: {0}'.
                             format(containers_name))

    def set_ids(self, ids):
        self.ids = ids
        if self.ids is None:
            self.ids = self.containers.ids
        for cid in self.ids:
            if cid not in self.containers.ids:
                raise ValueError('Id not match between '
                                 'containers {0} and exec {1}'.
                                 format(self.containers.get_name(),
                                        self.get_name()))

    def add_command(self, cmd):
        self.commands.append(cmd)

    def add_expect(self, expect):
        self.expects.append(expect)

    def run_internal(self):
        for i, name in enumerate(self.containers.get_container_names()):
            docker_exec = DockerExec(name)
            curr_id = self.ids[i]
            out = []
            err = []
            for cmd in self.commands:
                cmd = re.sub(self.sub_regex, str(curr_id), cmd)
                docker_exec.run(cmd, out, err)
            self.out_msgs.extend(out)
            self.err_msgs.extend(err)
            self.pass_expect_or_die(out, str(curr_id))

    def pass_expect_or_die(self, out, curr_id):
        out_idx = 0
        expect_idx = 0
        while (out_idx < len(out)) and (expect_idx < len(self.expects)):
            out_string = out[out_idx]
            expect_regex = self.expects[expect_idx]
            expect_regex = re.sub(self.sub_regex, curr_id, expect_regex)
            if re.search(expect_regex, out_string) is not None:
                expect_idx += 1
            out_idx += 1
        if expect_idx < len(self.expects):
            expect_regex = self.expects[expect_idx]
            expect_regex = re.sub(self.sub_regex, curr_id, expect_regex)
            raise ValueError('Out not matching expected. Unmatched: {0}; out:{1}'.
                             format(expect_regex, get_pretty_lines(out, 20)))
