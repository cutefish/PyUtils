import re
import xml.etree.ElementTree as ET



class Attribs(object):
    def __init__(self):
        pass

    def add_required(self, key, valfunc=str):
        pass

    def add_optional(self, key, default, valfunc=str):
        pass

    def parse(self, elem):
        pass

    def get(self):
        pass


def ConfElem(object):
    def __init__(self):
        self.attribs = Attribs()
        self.elems = {}


def Configure(ConfElem):
    def __init__(self):
        super(Configure, self).__init__()
        self.attribs.add_required('name')
        self.elems.add
















class Configure(ConfElem):
    def __init__(self):
        self.attrib_tag('name', required=True)
        self.add_elem('image', ImageConf, )
        self.add_elem('containers', ContainersConf)

    def parse(self, cfg_file):
        tree = ET.parse(cfg_file)
        root = tree.getroot()
        if root.tag != self.elem_tag:
            raise SyntaxError('Expected root tag: {0}, got: {1}'.
                              format(self.elem_tag, root.tag))
        self.read(root)
        self.resolve()

    def get_name(self):
        return self.attrs['name'].get()

    def get_tmpdir(self):
        return self.attrs['tmpdir'].get()

    def get_tasks(self):
        for elem in self.elems:
            yield elem




























class ConfElem(object):
    def __init__(self, name):
        self.name = name

class Properties(object):
    def __init__(self):
        pass


class Elem(object):
    def __init__(self, properties):
        self.properties = properties
        self.attrs = {}
        self.elem_classes = {}
        self.elems = []

    def expand_var(self, string):
        for var, val in self.properties.iteritems():
            string = re.sub('\${{{0}}}'.format(var), val, string)
        return string

    def get_attr(self, elem, key):
        if key not in elem.attrib:
            raise SyntaxError('Attribute {0} not found in {1}: {2}'.
                              format((key, elem, elem.attrib)))
        return self.expand_var(elem.attrib[key])

    def setstr(self, attr, val):
        attr.val = val

    def setstrlst(self, attr, val):
        parts = val.split(',')
        parts = map(lambda p : p.strip(), parts)
        attr.val.extend(parts)

    def setdir(self, attr, val):
        path = os.path.abspath(os.path.expanduser(val))
        attr.val = path

    def setattrs(self, attr, elem):
        attr.val.update(elem.attrib)

    def read(self, root):
        for key, val in root.attrib.iteritems():
            if key not in self.attrs:
                raise SyntaxError(
                    'Unknown attrib key {0} for {1}. Expected: {2}.'.
                    format(key, root.tag, self.attrs.keys()))
            self.attrs[key].update(val)
        for child in root:
            if ((child.tag not in self.attrs) and
                (child.tag not in self.elem_classes)):
                raise SyntaxError(
                    'Unknown tag {0} for {1}. Expected: {2}.'.
                    format(child.tag, root.tag,
                           self.attrs.keys() + self.elem_classes.keys()))
            if child.tag in self.attrs:
                self.attrs[child.tag].update(child)
            else:
                elem = self.elem_classes[key](self.properties)
                elem.read(child)
                self.elems.append(elem)


class Configure(ConfElem):
    def __init__(self):
        super(Configure, self).__init__(dict())
        self.tag = 'config'
        self.attrs = {
            'name' : ConfAttr(self.setstr, None),
            'tmpdir' : ConfAttr(self.setdir, None),
        }
        self.elem_classes = {
            'image' : ImageConf,
            'containers' : ContainersConf,
        }

    def parse(self, cfg_file):
        self.read_properties(root)
        self.read(root)

    def read_properties(self, root):
        for prop in root.iter('property'):
            self.properties[self.get_attr(prop, 'name')] = self.get_attr(prop, 'value')
        for key, val in self.properties.iteritems():
            self.properties[key] = self.expand_var(val)


class ImageConf(ConfElem):
    def __init__(self, properties):
        super(ImageConf, self).__init__(properties)
        self.attrs = {
            'name' : AttrElem(self.setstr, None),
            'depends' : AttrElem(self.setstr, None),
            'install' : AttrElem(self.setstrlst, list()),
            'volume' : AttrElem(self.setstrlst, list()),
            'proxy' : AttrElem(self.setattrs, dict()),
            'startup' : AttrElem(self.setattrs, dict()),
        }

    def get_name(self):
        return self.attrs['name'].get()

    def get_depends(self):
        return self.attrs['depends'].get()

    def get_install(self):
        return self.attrs['install'].get()

    def get_volume(self):
        return self.attrs['volume'].get()

    def get_proxy(self, proxy_name):
        return self.attrs['proxy'].get().get(proxy_name)



