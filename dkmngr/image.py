import os
import re


class ImageFactory(object):
    def __init__(self, src_dir, dst_dir):
        self.src_dir = src_dir
        self.dst_dir = '{0}/images'.format(dst_dir)
        os.makedirs(self.dst_dir)
        self.images = []
        self.add_image('builtin.dns', dns_image_content)

    def add_image(self, name, content):
        dst_dir = '{0}/{1}'.format(self.dst_dir, name)
        image = Image(name, [self.src_dir, "scripts"])
        image.init(content)
        image.setup(self.dst_dir)
        self.images.append(image)


dns_image_content = [
        'install bind9',
        'startup dns.py'
]


class Image(object):
    def __init__(self, name, lookup_path=[]):
        self.name = name
        self.lookup_paths = []
        self.lookup_paths.extend(lookup_paths)
        self.dockerfile_content = []
        self.external_files = []
        self.startup_files = []

    def init(self, content):
        content = list(content)
        self.dockerfile_content.append('FROM ubuntu:14.04')
        proxy = self.extract_proxy(content)
        if proxy is not None:
            self.dockerfile_content.append('ENV http_proxy {0}'.format(proxy))
            self.dockerfile_content.append('ENV https_proxy {0}'.format(proxy))
            self.dockerfile_content.append(
                'RUN echo "Acquire::http::Proxy \"{0}\";" > /etc/apt/apt.conf'.
                format(proxy))
        install = self.extract_install(content)
        if install is not None:
            self.dockerfile_content.append(
                'RUN apt-get update && apt-get install -y {0}'.
                format(install))
        self.dockerfile_content.append('RUN mkdir -p /opt/scripts')
        self.dockerfile_content.append('VOLUME ["/opt/lib"]')
        copy_files = self.extract_copy(content)
        self.external_files.extend(self.resolve_file_names(copy_files))
        for cpf in copy_files:
            self.dockerfile_content.append('COPY {0} /opt/scripts'.format(cpf))
        self.startup_files = self.extract_startup(content)
        self.external_files.extend(self.resolve_file_names(startup_files))
        for stf in self.startup_files:
            self.dockerfile_content.append('COPY {0} /opt/scripts'.format(stf))
        self.dockerfile_content.append(
            'ENTRYPOINT ["sh", "/opt/image_{0}_startup.sh"]'.
            format(self.name))

    def extract_proxy(self, content):
        vals = self.extract_lines(content, 'proxy')
        if len(vals) > 1:
            raise ValueError('Duplicated proxy: {0}'.format(vals))
        if len(vals) == 1:
            return vals[0]
        else:
            return None

    def extract_install(self, content):
        vals = self.extract_lines(content, 'install')
        if len(vals) == 0:
            return None
        return ' '.join(vals)

    def extract_copy(self, content):
        return self.extract_lines(content, 'copy')

    def extract_startup(self, content):
        return self.extract_lines(content, 'startup')

    def extract_lines(self, content, prefix):
        vals = []
        lines = filter(lambda l : l.startswith(prefix), content)
        for line in lines:
            line = line[len(prefix):].strip()
            parts = re.split('\s+', line)
            parts = map(lambda w : w.strip(), parts)
            vals.extend(parts)
        return vals

    def resolve_file_names(self, nlist):
        names = []
        for name in nlist:
            names.append(self.resolve_file_name(name))
        return names

    def resolve_file_name(self, name):
        if os.path.isabs(name):
            if os.path.exists(name):
                return name
            else:
                raise ValueError('Path not found: {0}'.format(name))
        for root in self.lookup_paths:
            for root, _, files in os.walk(root):
                if name in files:
                    return '{0}/{1}'.format(root, name)
        raise ValueError('Cannot find {0} in {1}'.
                         format(name, self.lookup_paths))

    def setup(self, dst):
        os.makedirs(dst)
