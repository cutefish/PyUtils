"""
exp.record

Processing text as records.

"""

import re

class RecordContext(object):
    def __init__(self, start, end):
        self.startRe = re.compile(start)
        self.endRe = re.compile(end)

    def isRecordStart(self, line):
        return self.startRe.search(line) != None

    def isRecordEnd(self, line):
        return self.endRe.search(line) != None

class RecordReader(object):
    def __init__(self, fd, context):
        self.fd = fd
        self.context = context
        self.recordlines = None

    def next(self):
        """
        Read the next record.

        Illegal records missing its start and end contexts are thrown away.

        """
        isInRecord = False
        while True:
            line = fd.nextline()
            #no line to read
            if line == '':
                return False
            #state transitions:
            # (not isInRecord, start) -> isInRecord, clear lines
            # (isInRecord, start)     -> isInRecord, clear lines
            # (not isInRecord, line)  -> not isInRecord
            # (isInRecord, line)      -> isInRecord, append line
            # (not isInRecord, end)   -> not isInRecord
            # (isInRecord, end)       -> not isInRecord, return
            if self.context.isRecordStart(line):
                isInRecord = True
                self.recordlines = []
            if isInRecord:
                self.recordlines.append(line)
                if self.context.isRecordEnd(line):
                    return True

    def getLines(self):
        return list(self.recordlines)
