import os
import re
import xml.etree.ElementTree as ET

from task import ImageBuildTask
from task import DnsImageBuildTask
from task import ContainersRunTask
from task import ContainersCmdTask
from docker import IPLocator


class Attribs(dict):
    def __init__(self, properties):
        super(Attribs, self).__init__()
        self.properties = properties
        self.required = {}
        self.optional = {}
        self.add_optional('description')

    def add_required(self, key, valfunc=str):
        self.required[key] = valfunc

    def add_optional(self, key, default=None, valfunc=str):
        self.optional[key] = (default, valfunc)

    def read_elem(self, elem):
        for key, val in elem.attrib.iteritems():
            val = self.expand_var(val)
            if key in self.required:
                self[key] = self.required[key](val)
            elif key in self.optional:
                self[key] = self.optional[key][1](val)
        for key in self.required:
            if key not in self.keys():
                raise SyntaxError('Attribute {0} is required for {1}'.
                                  format(key, elem.tag))
        for key in self.optional:
            if key not in self.keys():
                self[key] = self.optional[key][0]

    def expand_var(self, var):
        for key, val in self.properties.iteritems():
            var = re.sub('\${{{0}}}'.format(key), val, var)
        return var

    @classmethod
    def str2list(cls, string):
        parts = string.split(',')
        parts = map(lambda w : w.strip(), parts)
        return parts

    @classmethod
    def str2path(cls, string):
        return os.path.abspath(os.path.expanduser(string))

    @classmethod
    def str2paths(cls, string):
        parts = cls.str2list(string)
        parts = map(lambda p : os.path.abspath(os.path.expanduser(p)),
                    parts)
        return parts


class ExecConfHelper(object):
    def build(self, execution, cfg_file):
        tree = ET.parse(cfg_file)
        root = tree.getroot()
        ExecutionHandler().handle(root, execution)


class ExecutionHandler(object):
    def __init__(self):
        self.attribs = Attribs(dict())
        self.attribs.add_required('name')
        self.attribs.add_optional('tmpdir')
        self.properties = {}

    def handle(self, root, execution):
        self.attribs.read_elem(root)
        execution.set_name(self.attribs['name'])
        execution.set_tmpdir(self.attribs['tmpdir'])
        prop_attribs = Attribs(self.properties)
        prop_attribs.add_required('name')
        prop_attribs.add_required('value')
        proxy_attribs = Attribs(self.properties)
        proxy_attribs.add_optional('http')
        proxy_attribs.add_optional('https')
        for elem in root:
            if elem.tag == 'property':
                prop_attribs.read_elem(elem)
                self.properties[prop_attribs['name']] = \
                    prop_attribs['value']
            elif elem.tag == 'proxy':
                proxy_attribs.read_elem(elem)
                execution.set_proxy(proxy_attribs)
            elif elem.tag == 'image':
                task = ImageBuildTask(execution)
                handler = ImageHandler(self.properties)
                handler.handle(elem, task)
                execution.add_task(task)
            elif elem.tag == 'containers':
                task = ContainersRunTask(execution)
                handler = ContainersHandler(self.properties)
                handler.handle(elem, task)
                execution.add_task(task)
            elif elem.tag == 'exec':
                task = ContainersCmdTask(execution)
                handler = ContainersCmdHandler(self.properties)
                handler.handle(elem, task)
                execution.add_task(task)
            else:
                raise SyntaxError('Unknown tag {0} in execution configure.'.
                                  format(elem.tag))


class TaskElemHandler(object):
    def __init__(self, properties):
        self.attribs = Attribs(properties)
        self.attribs.add_required('name')
        self.attribs.add_optional('depends', list(), Attribs.str2list)

    def handle(self, root, task):
        self.attribs.read_elem(root)
        task.set_name(self.attribs['name'])
        task.set_depnames(self.attribs['depends'])


class ImageHandler(TaskElemHandler):
    def __init__(self, properties):
        super(ImageHandler, self).__init__(properties)
        self.install_attr = Attribs(properties)
        self.install_attr.add_required('packages', Attribs.str2list)
        self.startup_attr = Attribs(properties)
        self.startup_attr.add_required('scripts', Attribs.str2list)
        self.startup_attr.add_required('paths', Attribs.str2paths)
        self.volume_attr = Attribs(properties)
        self.volume_attr.add_required('paths', Attribs.str2paths)
        self.copy_attr = Attribs(properties)
        self.copy_attr.add_required('src', Attribs.str2path)
        self.copy_attr.add_required('dst', Attribs.str2path)

    def handle(self, root, img_task):
        super(ImageHandler, self).handle(root, img_task)
        for elem in root:
            if elem.tag == 'install':
                self.install_attr.read_elem(elem)
                img_task.set_install(self.install_attr['packages'])
            elif elem.tag == 'startup':
                self.startup_attr.read_elem(elem)
                scripts = self.startup_attr['scripts']
                search_paths = self.startup_attr['paths']
                script_abs_paths = self.resolve_paths(scripts, search_paths)
                img_task.set_startup_scripts(scripts)
                img_task.copy_to_startupdir(script_abs_paths)
            elif elem.tag == 'volume':
                self.volume_attr.read_elem(elem)
                img_task.set_volumes(self.volume_attr['paths'])
            elif elem.tag == 'copy':
                self.copy_attr.read_elem(elem)
                img_task.copy(self.copy_attr['src'], self.copy_attr['dst'])
            else:
                raise SyntaxError('Unknown tag {0} for image task'.
                                  format(elem.tag))

    def resolve_paths(self, basenames, search_paths):
        results = []
        for target in basenames:
            found = False
            for path in search_paths:
                for dirpath, dirnames, filenames in os.walk(path):
                    if target in filenames:
                        results.append('{0}/{1}'.format(dirpath, target))
                        found = True
                        break
                if found:
                    break
            if not found:
                raise OSError('Cannot find {0} in {1}'.
                              format(target, search_paths))
        return results


class ContainersHandler(TaskElemHandler):
    def __init__(self, properties):
        super(ContainersHandler, self).__init__(properties)
        self.attribs.add_required('image')
        self.attribs.add_required('ids', lambda x : list(eval(x)))
        self.attribs.add_optional('wait', 0, int)
        self.container_attr = Attribs(properties)
        self.container_attr.add_required('name')
        self.volume_attr = Attribs(properties)
        self.volume_attr.add_required('src', Attribs.str2path)
        self.volume_attr.add_required('dst', Attribs.str2path)
        self.env_attr = Attribs(properties)
        self.env_attr.add_required('name')
        self.env_attr.add_required('value')

    def handle(self, root, ctn_task):
        super(ContainersHandler, self).handle(root, ctn_task)
        ctn_task.set_image(self.attribs['image'])
        ctn_task.set_ids(self.attribs['ids'])
        ctn_task.set_wait(self.attribs['wait'])
        for elem in root:
            if elem.tag == 'container':
                self.container_attr.read_elem(elem)
                ctn_task.set_name_pattern(self.container_attr['name'])
            elif elem.tag == 'volume':
                self.volume_attr.read_elem(elem)
                ctn_task.add_volume_mapping(self.volume_attr['src'],
                                            self.volume_attr['dst'])
            elif elem.tag == 'env':
                self.env_attr.read_elem(elem)
                ctn_task.add_env(self.env_attr['name'], self.env_attr['value'])
            else:
                raise SyntaxError('Unknown tag {0} containers task'.
                                  format(elem.tag))


class ExecDnsHelper(object):
    def __init__(self, execution):
        self.execution = execution
        self.container_name = 'dns-server'

    def setup_dns(self):
        ctns_tasks = self.get_containers()
        mapping = self.assign_ip(ctns_tasks)
        img_task = self.add_dns_image(mapping)
        self.add_dns_container(mapping, img_task, ctns_tasks)

    def get_containers(self):
        ctns_tasks = []
        for task in self.execution.get_tasks():
            if isinstance(task, ContainersRunTask):
                ctns_tasks.append(task)
        return ctns_tasks

    def assign_ip(self, ctns_tasks):
        mapping = {}
        iplocator = IPLocator()
        mapping[self.container_name] = iplocator.next_ip()
        for task in ctns_tasks:
            names = task.get_container_names()
            ips = []
            for name in names:
                ip = iplocator.next_ip()
                mapping[name] = ip
                ips.append(ip)
            task.set_ip_addresses(ips)
        return mapping

    def add_dns_image(self, mapping):
        img_task = DnsImageBuildTask(self.execution, mapping)
        self.execution.add_task(img_task)
        return img_task

    def add_dns_container(self, mapping, img_task, ctns_tasks):
        run_task = ContainersRunTask(self.execution)
        run_task.set_image(img_task.get_name())
        run_task.set_name('dns-container')
        run_task.set_ids([''])
        run_task.set_name_pattern(self.container_name)
        self.execution.add_task(run_task)
        self.execution.add_dependency(run_task, ctns_tasks)
        run_task.set_ip_addresses([mapping[self.container_name]])
        for task in ctns_tasks:
            task.add_depend(run_task)
            task.set_dns(mapping[self.container_name])


class ContainersCmdHandler(TaskElemHandler):
    def __init__(self, properties):
        super(ContainersCmdHandler, self).__init__(properties)
        self.attribs.add_required('containers')
        self.attribs.add_optional('ids', valfunc=eval)
        self.run_attr = Attribs(properties)
        self.run_attr.add_required('cmd')
        self.expect_attr = Attribs(properties)
        self.expect_attr.add_required('value')

    def handle(self, root, cmd_task):
        super(ContainersCmdHandler, self).handle(root, cmd_task)
        self.attribs.read_elem(root)
        cmd_task.set_containers(self.attribs['containers'])
        cmd_task.set_ids(self.attribs['ids'])
        for elem in root:
            if elem.tag == 'run':
                self.run_attr.read_elem(elem)
                cmd_task.add_command(self.run_attr['cmd'])
            elif elem.tag == 'expect':
                self.expect_attr.read_elem(elem)
                cmd_task.add_expect(self.expect_attr['value'])
            else:
                raise SyntaxError('Unknown tag {0} for containers cmd task'.
                                  format(elem.tag))
