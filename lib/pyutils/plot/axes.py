"""
plot.axes

"""

from pyutils.plot.line import Line2D

class Axes(object):
    """Wrapper object for the matplotlib.axes.Axes."""
    LINE2D = "line2D"
    XLABEL = "xlabel"
    XTICKS = "xticks"
    XTICKLABELS = "xticklabels"
    YLABEL = "ylabel"
    YTICKS = "yticks"
    YTICKLABELS = "yticklabels"
    KEYS = [LINE, XLABEL, XTICKS, XTICKLABELS, YLABEL, YTICKS, YTICKLABELS]
    def __init__(self, axes, figure):
        self._axes = axes
        self._figure = figure
        self._lines = []

    def getAxes(self):
        return self._axes

    @property
    def figure(self):
        return self._figure

    def addLine(self, line):
        self._lines.append(line)

    @classmethod
    def draw(cls, xdim, ydim, acfg, parent):
        """Draw an axes with acfg on parent figure. 

        acfg    -- Axes config ptree node. 
                   The ptree node should have a form of axes.idx.*
        parent  -- Parent figure object
        
        """
        fig = parent.getFigure()
        props = {}
        idx = int(acfg.key)
        axes = fig.add_subplot(xdim, ydim, idx)
        for child in acfg.children:
            key = child.key
            val = child.val
            if key == cls.LINE2D:
                for line in child.children:
                    Line2D.draw(line, axes)
            if key == XLABEL:
                plt.setp(axes, xlabel=val)
            if key == XTICKS:
                plt.setp(axes, xticks=val)
            if key == XTICKLABELS:
                plt.setp(axes, xticklabels=val)
            if key == YLABEL:
                plt.setp(axes, ylabel=val)
            if key == YTICKS:
                plt.setp(axes, yticks=val)
            if key == YTICKLABELS:
                plt.setp(axes, yticklabels=val)
        newaxes = Line2D(axes, fig)
        parent.addAxes(newaxes)
        return newaxes
            

