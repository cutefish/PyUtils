"""
common.iterator
"""
class MultiListIterator(object):
    """ Iterator that goes through multiple lists.

    Constructor args:
        lists -- the list
        order -- the order of list to iterate. Lower order lists will
        exhaust first.

    """
    def __init__(self, lists, order=None, sticks={}):
        self.keys = []
        self.lists = []
        self.sticks = {}
        #build an ordered list
        if not isinstance(lists, dict):
            tmp = {}
            for i, l in enumerate(lists):
                tmp[i] = l
        else:
            tmp = lists
        if order is None:
            order = range(len(tmp))
        for key in order:
            try:
                self.lists.append(tmp[key])
                if key in sticks:
                    sticklist = []
                    for s in sticks[key]:
                        if len(tmp[s]) < len(tmp[key]):
                            raise ValueError('lists %s and %s cannot stick \
                                             together because len(%s) \
                                             is smaller')
                        sticklist.append(tmp[s])
                        tmp.pop(s, None)
                    self.sticks[key] = sticklist
                tmp.pop(key, None)
            except KeyError:
                raise KeyError('order list incorrect with key %s: ' %key)
        self.keys = order
        self.indices = [0] * len(self.lists)
        self.indices[0] = -1

    def reset(self):
        self.indices = [0] * len(self.lists)
        self.indices[0] = -1

    def next(self):
        """Return the next elements of lists.

        Elements are returned according to order. Stick elements are bundled
        together. For example, num = [1,2,3] alpha = [a, b, c] Alpha = [A, B,
        C], if num and alpha are sticked together; order is num, Alpha, next
        will return [1, a, A]. If no more elements, None is returned.

        """
        carry = False
        for i, idx in enumerate(self.indices):
            carry = False
            idx = idx + 1
            if idx < len(self.lists[i]):
                self.indices[i] = idx
                break
            else:
                self.indices[i] = 0
                carry = True
        if carry is True:
            return None
        curr = []
        for i, l in enumerate(self.lists):
            key = self.keys[i]
            idx = self.indices[i]
            curr.append(self.lists[i][idx])
            if self.sticks.has_key(key):
                for sl in self.sticks[key]:
                    curr.append(sl[idx])
        return curr

def testMultiListIterator():
    lists = [[0, 1, 2], [10, 11, 12]]
    it = MultiListIterator(lists)
    while(True):
        curr = it.next()
        if curr is None:
            break
        print curr
    it.reset()
    print
    while(True):
        curr = it.next()
        if curr is None:
            break
        print curr
    print
    it = MultiListIterator(lists, [1, 0])
    while(True):
        curr = it.next()
        if curr is None:
            break
        print curr
    print
    it = MultiListIterator({'l0':[0, 1, 2], 'l1':[10, 11, 12]},
                           ['l1', 'l0'])
    while(True):
        curr = it.next()
        if curr is None:
            break
        print curr

def main():
    testMultiListIterator()

if __name__ == '__main__':
    main()
