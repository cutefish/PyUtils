import logging
import shlex
from subprocess import Popen
import sys
from time import sleep
from threading import Thread

class CmdObject(object):
    def __init__(self, command):
        self.command = command
        self.proc = None
        self.stdout = None
        self.stderr = None
        self.retcode = None

    @property
    def cmd(self):
        return str(self.command)

    def startup(self):
        pass

    def run(self):
        pass

    def cleanup(self):
        pass

    @property
    def output(self):
        return []

class CmdThread(Thread):
    def __init__(self, cmdobj):
        Thread.__init__(self)
        self.cmdobj = cmdobj
        self.logger = logging.getLogger(self.__class__.__name__)
        self.closed = False
        self.retcode = None

    @property
    def output(self):
        return self.cmdobj.output

    def run(self):
        self.cmdobj.startup()
        self.logger.info('start: %s'%self.cmdobj.cmd)
        proc = Popen(shlex.split(self.cmdobj.command),
                     stdout=self.cmdobj.stdout, stderr=self.cmdobj.stderr)
        self.cmdobj.proc = proc
        while not self.closed:
            #periodically check the status of execution
            self.cmdobj.retcode = proc.poll()
            if self.cmdobj.retcode is not None:
                break
            #run the object function
            self.cmdobj.run()
            sleep(1)
        self.cmdobj.cleanup()
        self.logger.info('end: %s'%self.cmdobj.cmd)

    def close(self):
        self.closed = True

def runCommands(commands, numThreads):
    threads = set([])
    finished = []
    try:
        while True:
            #first remove finished threads
            for thread in list(threads):
                if not thread.isAlive():
                    threads.remove(thread)
                    finished.append(thread)
            #check terminate condition
            if len(threads) == 0 and len(commands) == 0:
                break
            #try to launch new commands if we can
            if len(threads) < numThreads and len(commands) != 0:
                for i in range(len(threads), numThreads):
                    command = commands.pop(0)
                    thread = CmdThread(command)
                    thread.start()
                    threads.add(thread)
                    if len(commands) == 0:
                        break
            sleep(1)
    except (Exception, BaseException) as e:
        print e
        for thread in threads:
            thread.close()
    finally:
        for thread in threads:
            thread.join()
            assert not thread.isAlive()
        #print output
        for thread in finished:
            for item in thread.output:
                sys.stdout.write(item)
        sys.stdout.flush()
