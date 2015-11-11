import sys

from configure import Configure, ImageTarget


def main():
    src = sys.argv[1]
    cfg_file = '{0}/config.xml'.format(src)
    config = Configure()
    config.read(cfg_file)
    print 'properties', config.properties
    for t in config.targets:
        lst = []
        for p, d in t.attrs.iteritems():
            lst.append(
                '{0} : {{{1}}}'.
                format(p, ','.
                       join(['{0}:{1}'.
                             format(k, str(v)) for k, v in d.iteritems()])))
        print ','.join(lst)


if __name__ == '__main__':
    main()
