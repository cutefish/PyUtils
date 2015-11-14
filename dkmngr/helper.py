import os
import re
import xml.etree.ElementTree as ET

from task import ImageBuildTask
from task import ContainersRunTask


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
        for elem in root:
            if elem.tag == 'property':
                prop_attribs.read_elem(elem)
                self.properties[prop_attribs['name']] = \
                    prop_attribs['value']
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
        self.proxy_attr = Attribs(properties)
        self.proxy_attr.add_optional('http')
        self.proxy_attr.add_optional('https')
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
            if elem.tag == 'proxy':
                self.proxy_attr.read_elem(elem)
                img_task.set_proxy(self.proxy_attr)
            elif elem.tag == 'install':
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
                raise SyntaxError('Unknown tag {0} image task'.format(elem.tag))

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
        self.range_attr = Attribs(properties)
        self.range_attr.add_required('var')
        self.range_attr.add_required('expr')
        self.name_attr = Attribs(properties)
        self.name_attr.add_required('pattern')
        self.volume_attr = Attribs(properties)
        self.volume_attr.add_required('src', Attribs.str2path)
        self.volume_attr.add_required('dst', Attribs.str2path)
        self.env_attr = Attribs(properties)
        self.env_attr.add_required('name')
        self.env_attr.add_required('value')

    def handle(self, root, ctn_task):
        super(ContainersHandler, self).handle(root, ctn_task)
        ctn_task.set_image(self.attribs['image'])
        for elem in root:
            if elem.tag == 'range':
                self.range_attr.read_elem(elem)
                ctn_task.set_range_regex('\${0}'.format(self.range_attr['var']))
                ctn_task.set_range_vals(eval(self.range_attr['expr']))
            elif elem.tag == 'name':
                self.name_attr.read_elem(elem)
                ctn_task.set_name_pattern(self.name_attr['pattern'])
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
    def setup_dns(self, execution):
        pass
