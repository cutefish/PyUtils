import logging


class Execution(object):
    def __init__(self):
        self.name = None
        self.tmpdir = None
        self.tasks = {} # name : task
        self.depends = {} # T : tasks depends on T
        self.ready = []
        self.wait = set([])
        self.success = set([])
        self.fail = set([])
        self.stopped = False
        self.logger = logging.getLogger('exec')

    def set_name(self, name):
        self.name = name

    def set_tmpdir(self, tmpdir):
        self.tmpdir = tmpdir

    def add_task(self, task):
        name = task.get_name()
        assert name is not None
        if name in self.tasks:
            raise ValueError('Conflicted task name: {0}'.format(name))
        self.tasks[name] = task
        for depname in task.depnames:
            if depname not in self.tasks:
                raise SyntaxError('Unknown task name: {0}'.format(depname))
            deptask = self.tasks[depname]
            if deptask not in self.depends:
                self.depends[deptask] = []
            self.depends[deptask].append(task)
            task.add_depend(deptask)
        if len(task.depnames) == 0:
            self.ready.append(task)

    def run(self):
        while not self.stopped:
            task = self.ready.pop(0)
            self.logger.info('\n{0}:'.format(task.get_name()))
            task.run()
            self.done_task(task)

    def done_task(self, task):
        for msg in task.get_out_msgs():
            self.logger.info('\t[out]: {0}'.format(msg))
        for msg in task.get_out_msgs():
            self.logger.info('\t[err]: {0}'.format(msg))
        if task.is_failed():
            task.fail_action.do()
        if not self.stopped:
            self.add_ready_tasks(task)
        if len(self.ready) == 0:
            self.stopped = True

    def add_ready_tasks(self, finished):
        if finished not in self.depends:
            return
        for dep in self.depends[finished]:
            if dep.is_done():
                continue
            ready = True
            for task in dep.get_depends():
                if not task.is_done():
                    ready = False
            if ready:
                self.ready.append(dep)
        del self.depends[finished]


class TaskFailAction(object):
    def __init__(self, task):
        self.task = task
        self.execution = task.execution

    def do(self):
        self.execution.logger.info('Task {0} failed.'.
                                   format(self.task.get_name()))


class StopExecutionAction(TaskFailAction):
    def do(self):
        super(StopExecutionAction, self).do()
        self.execution.logger.info('Stopping execution.')
        self.execution.stopped = True

