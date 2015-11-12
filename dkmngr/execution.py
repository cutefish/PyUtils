class Execution(object):
    def __init__(self):
        self.name = None
        self.tmpdir = None
        self.tasks = []

    def set_name(self, name):
        self.name = name

    def set_tmpdir(self, tmpdir):
        self.tmpdir = tmpdir

    def add_task(self, task):
        self.tasks.append(task)


