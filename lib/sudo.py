import re
import pexpect
import getpass
import sys

PASSWD_PATTERNS = [re.compile('.*passwd.*',re.IGNORECASE),
                   re.compile('.*password.*', re.IGNORECASE)]

def sudo(command):
    sudoCmd = "sudo " + command
    child = pexpect.spawn(sudoCmd)
    child.expect(PASSWD_PATTERNS)
    passWd = getpass.getpass("sudo password:")
    child.sendline(passWd)
    returns = child.readlines()
    print returns

def main():
    sudo("cat /etc/passwd")

if __name__ == "__main__":
    main()


