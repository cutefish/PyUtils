"""
plot.bar

bar utilities.
"""
from pyutils.common.iterator import MultiListIterator

HATCHES =  ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']

LINE_STYLES = ['solid', 'dashed', 'dashdot', 'dotted']

COLORS = [
    'springgreen', 'orange', 'lightblue', 'hotpink', 'aquamarine',
    'greenyellow', 'rosybrown', 'azure', 'indianred', 'gold',
    'skyblue', 'tan',
]

class BarStyle(object):
    def __init__(self, edgecolor=None, facecolor=None,
                 hatch=None, linestyle=None):
        self._edgecolor = edgecolor
        self._facecolor = facecolor
        self._hatch = hatch
        self._linestyle = linestyle
    
    @property
    def edgecolor(self):
        return self._edgecolor

    @edgecolor.setter
    def edgecolor(self, edgecolor):
        self._edgecolor = edgecolor

    @property
    def facecolor(self):
        return self._facecolor

    @facecolor.setter
    def facecolor(self, facecolor):
        self._facecolor = facecolor

    @property
    def hatch(self):
        return self._hatch

    @hatch.setter
    def hatch(self, hatch):
        self._hatch = hatch

    @property
    def linestyle(self):
        return self._linestyle

    @linestyle.setter
    def linestyle(self, linestyle):
        self._linestyle = linestyle

    def __iter__(self):
        yield self._edgecolor
        yield self._facecolor
        yield self._hatch
        yield self._linestyle

    def __str__(self):
        return 'edgecolor=%s, facecolor=%s, hatch=%s, linestyle=%s' %(
            self._edgecolor, self._facecolor, self._hatch, self._linestyle)

class BarStyles(object):
    """
    A collection of bar styles to iterate through.

    Style key:
        edgecolor, facecolor, hatch, linestyle

    Constructor options:
        bs      --  a dictionary of bar styles
        order   --  the order of change when iterates
        stick   --  stick two styles together.
    """
    STYLE_KEYS = ['edgecolor', 'facecolor', 'hatch', 'linestyle']
    def __init__(self, bs={}, order=['hatch', 'facecolor',
                                     'edgecolor', 'linestyle'],
                 sticks={}):
        #validity check
        for key in bs.keys():
            if key not in BarStyles.STYLE_KEYS:
                raise KeyError('Invalid key for line style: %s' %key)
        for key in order:
            if key not in BarStyles.STYLE_KEYS:
                raise KeyError('Invalid key for line style: %s' %key)
        for key in sticks:
            if key not in BarStyles.STYLE_KEYS:
                raise KeyError('Invalid key for line style: %s' %key)
        #assign default styles
        self.bs = bs
        if not self.bs.has_key('edgecolor') or self.bs['edgecolor'] is None:
            self.bs['edgecolor'] = COLORS
        if not self.bs.has_key('facecolor') or self.bs['facecolor'] is None:
            self.bs['facecolor'] = COLORS
        if not self.bs.has_key('hatch') or self.bs['hatch'] is None:
            self.bs['hatch'] = HATCHES
        if not self.bs.has_key('linestyle') or self.bs['linestyle'] is None:
            self.bs['linestyle'] = LINE_STYLES
        #assign other attributes
        self.order = order
        #stick
        self.sticks = sticks
        #iterator
        self.it = MultiListIterator(bs, order, sticks=sticks)

    def next(self):
        vals = self.it.next()
        if vals is None:
            self.it.reset()
            vals = self.it.next()
        curr = BarStyle()
        order_idx = 0
        val_idx = 0
        while True:
            if val_idx == len(vals):
                break
            val = vals[val_idx]
            orderkey = self.order[order_idx]
            setattr(curr, orderkey, val)
            val_idx += 1
            order_idx += 1
            if self.sticks.has_key(orderkey):
                for key in self.sticks[orderkey]:
                    val = vals[val_idx]
                    setattr(curr, key, val)
                    val_idx += 1
        return curr
