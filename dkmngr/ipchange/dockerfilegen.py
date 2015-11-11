import sys


def genfile(name, proxy):
    lines = [
        'FROM ubuntu:14.04\n',
        '\n'
        'ENV http_proxy {0}\n'.format(proxy),
        'ENV https_proxy {0}\n'.format(proxy),
        ('RUN echo "Acquire::http::Proxy '
         '\\"{0}\\";" '
         '> /etc/apt/apt.conf\n'.format(proxy)),
        '\n'
        'RUN apt-get update && apt-get install -y bind9 openjdk-7-jdk host\n',
        '\n'
        'COPY entrypoint.py /sbin/entrypoint.py\n',
        '\n'
    ]
    if name == 'dns':
        lines.append('ENTRYPOINT ["python", "/sbin/entrypoint.py", "dns"]\n')
    else:
        lines.append('VOLUME ["/kvlib"]\n\n')
        lines.append('ENTRYPOINT ["python", "/sbin/entrypoint.py"]\n')
    with open('{0}/Dockerfile'.format(name), 'w') as writer:
        writer.writelines(lines)


def main():
    if len(sys.argv) != 3:
        print 'dockerfilegen <name> <proxy>'
        sys.exit()
    name = sys.argv[1]
    proxy = sys.argv[2]
    genfile(name, proxy)


if __name__ == '__main__':
    main()
