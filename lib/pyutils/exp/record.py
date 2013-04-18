"""
common.record

Processing text as records.

"""

import re

class RecordContext(object):
    def __init__(self, start, end):
        self.startRe = re.compile(start)
        if end == None:
            self.endRe = None
        else:
            self.endRe = re.compile(end)

    def isRecordStart(self, line):
        return self.startRe.search(line) != None

    def isRecordEnd(self, line):
        return self.endRe.search(line) != None

    def unknownRecordEnd(self):
        return self.endRe == None

class RecordReader(object):
    def __init__(self, fd, context):
        self.fd = fd
        self.context = context
        self.recordlines = None
        self.buf = []
        self.eof = False
        self.lineno = 0
        self.rstart = 0
        self.rend = 0

    def next(self):
        """
        Read the next record.

        Illegal records missing its start and end contexts are thrown away.

        """
        isInRecord = False
        while True:
            if len(self.buf) != 0:
                line = self.buf.pop(0)
            else:
                line = self.fd.readline()
                self.lineno += 1
            #no line to read
            if line == '':
                break
            #state transitions:
            # (not isInRecord, start) -> isInRecord, clear lines
            # (isInRecord, start)     -> isInRecord
            #                            if end, clear lines
            #                            if none end, buffer line, return
            # (not isInRecord, line)  -> not isInRecord
            # (isInRecord, line)      -> isInRecord, append line
            # (not isInRecord, end)   -> not isInRecord
            # (isInRecord, end)       -> not isInRecord, return
            if self.context.isRecordStart(line):
                if isInRecord:
                    if self.context.unknownRecordEnd():
                        self.buf.append(line)
                        self.rend = self.lineno - 1
                        return True
                self.rstart = self.lineno
                isInRecord = True
                self.recordlines = []
            if isInRecord:
                self.recordlines.append(line)
                if self.context.unknownRecordEnd():
                    continue
                if self.context.isRecordEnd(line):
                    self.rend = self.lineno
                    return True
        #end of file
        if not self.eof:
            self.eof = True
            #get last record if unknown end
            if self.recordlines != None and \
               len(self.recordlines) != 0 and \
               self.context.unknownRecordEnd():
                self.rend = self.lineno
                return True
        if self.eof:
            return False

    def getLines(self):
        return self.recordlines

    def currLineno(self):
        return self.lineno

    def getRecordLineRange(self):
        return self.rstart, self.rend

def testRecordReader():
    fd = open('/tmp/testrr', 'w')
    fd.write('##### START #####\n')
    fd.write('aaa\n')
    fd.write('bbb\n')
    fd.write('ccc\n')
    fd.write('##### END #####\n')
    fd.write('##### START #####\n')
    fd.write('ddd\n')
    fd.write('eee\n')
    fd.write('fff\n')
    fd.write('##### END #####\n')
    fd.write('##### START #####\n')
    fd.write('ggg\n')
    fd.write('hhh\n')
    fd.write('##### START #####\n')
    fd.write('iii\n')
    fd.write('jjj\n')
    fd.write('kkk\n')
    fd.write('##### END #####\n')
    fd.write('lll\n')
    fd.write('mmm\n')
    fd.write('##### END #####\n')
    fd.close()
    fd = open('/tmp/testrr', 'r')
    context = RecordContext('##### START #####',
                            '##### END #####')
    reader = RecordReader(fd, context)
    while(reader.next()):
        print reader.getLines()
        print reader.currLineno()
        print reader.getRecordLineRange()
    fd.close()
    print
    fd = open('/tmp/testrr', 'r')
    context = RecordContext('##### START #####', None)
    reader = RecordReader(fd, context)
    while(reader.next()):
        print reader.getLines()
        print reader.currLineno()
        print reader.getRecordLineRange()
    fd.close()

def main():
    testRecordReader()

if __name__ == '__main__':
    main()
