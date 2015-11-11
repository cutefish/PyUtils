import re
import sys

def main():
    if len(sys.argv) != 2:
        print 'checkfail <file>'
        sys.exit()
    filename = sys.argv[1]
    do_checkfail(filename)


def get_succ_seq():
    sequence = [
        ('dns image build', 'Successfully built [a-z0-9]+'),
        ('dns ifconfig', 'inet addr:[0-9]+\.[0-9]+\.0\.100'),
        ('dns /etc/hosts', '[0-9]+\.[0-9]+\.0\.100\s+dns\.kv dns'),
        ('dns dns.kv', 'dns.kv has address [0-9]+\.[0-9]+\.0\.100'),
        ('dns server0.kv', 'server0.kv has address [0-9]+\.[0-9]+\.0\.10')
    ]
    sequence.append(('server image build',
                     'Successfully built [a-z0-9]+'))
    for i in range(3):
        sequence.extend(
            [
                ('server{0} ifconfig'.format(i),
                 'inet addr:[0-9]+\.[0-9]+\.0\.1{0}'.format(i)),
                ('server{0} /etc/hosts'.format(i),
                 '[0-9]+\.[0-9]+\.0\.1{0}\s+server{0}\.kv server{0}'.format(i)),
                ('dns server{0}.kv'.format(i),
                 'server{0}.kv has address [0-9]+\.[0-9]+\.0\.1{0}'.format(i)),
                ('server{0} jps 1'.format(i),
                 '[0-9]+\s+(kvstore.jar|ManagedService)'),
                ('server{0} jps 2'.format(i),
                 '[0-9]+\s+(kvstore.jar|ManagedService)')
            ]
        )
    sequence.extend([
        ('client image build', 'Successfully built [a-z0-9]+'),
        ('client connect store', 'Connected to mystore'),
        ('client topo verification',
         'Verification complete, no violations'),
        ('client put', 'xiao'),
        ('client table create', 'mytable'),
    ])
    for i in range(3):
        sequence.extend(
            [
                ('server{0} flipip'.format(i),
                 'inet addr:[0-9]+\.[0-9]+\.1\.1{0}'.format(i)),
                ('server{0} flipip /etc/hosts'.format(i),
                 '[0-9]+\.[0-9]+\.1\.1{0}\s+server{0}\.kv server{0}'.format(i)),
                ('dns flip server{0}.kv 1.1'.format(i),
                 'Changed \[server{0}\s+IN\s+A.*0\.1{0}'.format(i)),
                ('dns flip server{0}.kv 1.2'.format(i),
                 'to\s+\[server{0}\s+IN\s+A.*1\.1{0}'.format(i)),
                ('dns flip server{0}.kv 2.1'.format(i),
                 'Changed \[0\.1{0}.*server{0}'.format(i)),
                ('dns flip server{0}.kv 2.2'.format(i),
                 'to\s+\[1\.1{0}.*server{0}'.format(i)),
                ('dns flip server{0}.kv 3.1'.format(i),
                 'Starting domain name service.*bind9'),
                ('dns flip server{0}.kv 3.2'.format(i), 'done'),
            ]
        )
    sequence.extend([
        ('client connect store after flip', 'Connected to mystore'),
        ('client topo verification after flip',
         'Verification complete, no violations'),
        ('client put after flip', 'xiao'),
        ('client table create after flip', 'mytable'),
    ])
    return sequence


def do_checkfail(filename):
    sequence = get_succ_seq()
    cidx = 0
    with open(filename, 'r') as reader:
        for line in reader:
            if cidx == len(sequence):
                print 'Test success.'
                break
            tag, regex = sequence[cidx]
            if re.search(regex, line):
                cidx += 1
                print 'Success: {0}'.format(tag)
    if cidx < len(sequence):
        raise RuntimeError('Failed: {0}'.format(sequence[cidx][0]))


if __name__ == '__main__':
    main()
