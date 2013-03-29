"""
plot.line

line utilities.
"""
from pyutils.common.iterator import MultiListIterator

LINE_MARKERS =  {
    0: 'tickleft', 1: 'tickright', 2: 'tickup', 3: 'tickdown', 
    4: 'caretleft', 'D': 'diamond', 6: 'caretup', 7: 'caretdown',
    's': 'square', '|': 'vline', 'x': 'x', 5: 'caretright', 
    '_': 'hline', '^': 'triangle_up', 'd': 'thin_diamond', 'h': 'hexagon1', 
    '+': 'plus', '*': 'star', ',': 'pixel', 'o': 'circle', 
    '.': 'point', '1': 'tri_down', 'p': 'pentagon', '3': 'tri_left', 
    '2': 'tri_up', '4': 'tri_right', 'H': 'hexagon2', 'v': 'triangle_down', 
    '8': 'octagon', '<': 'triangle_left', '': 'nothing', 
    #'None': 'nothing', None: 'nothing', ' ': 'nothing', 
}

LINE_STYLES = {
    '-': 'solid', '--': 'dashed', '-.': 'dashed_dot', ':': 'dotted',
    '': 'draw nothing',
    #'None': 'draw nothing', ' ': 'draw nothing', 
}

LINE_COLORS = [
    'springgreen', 'orange', 'lightblue', 'hotpink', 'aquamarine',
    'greenyellow', 'rosybrown', 'azure', 'indianred', 'gold',
    'skyblue', 'tan',
]

class LineStyle(object):
    def __init__(self, marker=None, conn=None, color=None):
        self._marker = marker
        self._conn = conn
        self._color = color
    
    @property
    def marker(self):
        return self._marker

    @marker.setter
    def marker(self, marker):
        self._marker = marker

    @property
    def conn(self):
        return self._conn

    @conn.setter
    def conn(self, conn):
        self._conn = conn

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color

    def __iter__(self):
        yield self._marker
        yield self._conn
        yield self._color

    def __str__(self):
        return 'marker=%s, ls=%s, color=%s' %(
            self._marker, self._conn, self._color)

class LineStyles(object):
    """
    A collection of line styles to iterate through.

    Style key:
        marker, color, conn

    Constructor options:
        ls      --  a dictionary of line styles
        order   --  the order of change when iterates
        stick   --  stick two styles together.
    """
    STYLE_KEYS = ['marker', 'color', 'conn']
    def __init__(self, ls={}, order=['marker', 'color', 'conn'], sticks={}):
        #validity check
        for key in ls.keys():
            if key not in LineStyles.STYLE_KEYS:
                raise KeyError('Invalid key for line style: %s' %key)
        for key in order:
            if key not in LineStyles.STYLE_KEYS:
                raise KeyError('Invalid key for line style: %s' %key)
        for key in sticks:
            if key not in LineStyles.STYLE_KEYS:
                raise KeyError('Invalid key for line style: %s' %key)
        #assign default styles
        self.ls = ls
        if not self.ls.has_key('marker') or self.ls['marker'] is None:
            self.ls['marker'] = LINE_MARKERS.keys()
        if not self.ls.has_key('conn') or self.ls['conn'] is None:
            self.ls['conn'] = LINE_STYLES.keys()
        if not self.ls.has_key('color') or self.ls['color'] is None:
            self.ls['color'] = LINE_COLORS
        #assign other attributes
        self.order = order
        #stick
        self.sticks = sticks
        #iterator
        self.it = MultiListIterator(ls, order, sticks=sticks)

    def next(self):
        vals = self.it.next()
        if vals is None:
            self.it.reset()
            vals = self.it.next()
        curr = LineStyle()
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
