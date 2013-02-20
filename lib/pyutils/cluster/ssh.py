"""
cluster.ssh.py

ssh related utils.

"""
import sys
import subprocess

class SSHOption:
    """ Options of the ssh command.  """
    DEFAULT_SSH_OPTION_KEY = "DEFAULT_SSH_OPTION"

    OPT_NO_STRICT_HOST_KEY_CHECKING = "-o StrictHostKeyChecking=no"
    OPT_NO_USER_KNOWN_HOSTS_FILE = "-o UserKnownHostsFile=/dev/null"

    def __init__(self, args=None, conf=None, 
                 key=DEFAULT_SSH_OPTION_KEY):
        self.options = self.findSSHOptions(args, conf)
        self.options = self.options.strip(' ')

    def findSSHOptions(self, args, conf, 
                       key=DEFAULT_SSH_OPTION_KEY):
        """Find the SSH option setting.

        SSH options can be set in args, configuration or system environment.
        The overwrite priority is args > configuration > system environement.

        Returns an option string or empty string."""
        if args != None:
            return args
        ret = None
        if conf != None:
            ret = conf.get(key)
        if ret != None:
            return ret
        if os.environ[key] != None:
            return os.environ[key]
        return ""

    def addOption(self, opt):
        self.options = '%s %s' %(self.options, opt.strip(' '))

    def __str__(self):
        if self.options == "":
            return " "
        return ' %s ' %self.options.strip(' ')

class SSHCommand:
    """ SSH Command, which can be executed remotely on a node through ssh. """
    def __init__(self, user, hostname, command, options=None, 
                 stdout=sys.stdout):
        self.user = user.strip(' ')
        self.hostname = hostname.strip(' ')
        self.command = command.strip(' ')
        self.options = options
        self.stdout = stdout

    def checkOutput(self):
        """
        Run command and return its output as a byte string.

        If the return code was non-zero it rasies CalledProcessError. The
        CalledProcessError object will have the return code in the returncode
        attribute and any output in the output attribute.  
        """
        shell = 'ssh%s%s@%s %s' %(self.options, self.user, 
                                   self.hostname, self.command)
        print 'SSHCommand: %s' %shell
        return subprocess.check_output(shell.split(' '))

def main(ip, command):
    options = SSHOption("")
    options.addOption(SSHOption.OPT_NO_STRICT_HOST_KEY_CHECKING)
    options.addOption(SSHOption.OPT_NO_USER_KNOWN_HOSTS_FILE)
    options.addOption('-i /hadoop/ec2/mrioec2keypriv.pem')
    sshcmd = SSHCommand('ec2-user', ip, command, options)
    print sshcmd.checkOutput()

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

