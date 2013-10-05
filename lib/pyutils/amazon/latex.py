"""

latex.py

Latex Utilities.

"""

import pyutils.common.fileutils as fu
from pyutils.common.clirunnable import CliRunnable

class LatexRunnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'article': 'Generate a simple article template',
            'table' : 'Table Stub',
        }

    def article(self, argv):
        if len(argv) != 1:
            print 'latex article <path>'
            sys.exit(-1)
        fd = open(fu.normalizeName(argv[0]), 'w')
        fd.write('\documentclass[12pt]{article}\n')
        fd.write('\usepackage{amsthm}\n')
        fd.write('%\usepackage[margin=0.5in, paperwidth=9in, paperheight=12in]'
                 '{geometry}')
        fd.write('\usepackage{hyperref}\n')
        fd.write('\usepackage{url}\n')
        fd.write('\usepackage{setspace}\n')
        fd.write('%\doublespacing\n')
        fd.write('\n')
        fd.write('\\begin{document}\n')
        fd.write('\\title{Simple Article Template}\n')
        fd.write('\date{}\n')
        fd.write('\\author{Who Am I}\n')
        fd.write('\n\maketitle\n\n')
        fd.write('\n\n\n\n')
        fd.write('\\bibliographystyle{plain}\n')
        fd.write('\\bibliography{ref}\n')
        fd.write('\n')
        fd.write('\end{document}\n')
        fd.close()

    def table(self, argv):
        print '\\begin{table*}[!h]'
        print '\label{tab:label}'
        print '\caption{Table Caption}'
        print '\centering'
        print '\\begin{tabular}{|c|c|c|}'
        print '\hline'
        print '0, 0 & 0, 1 & 0, 2 \\\\'
        print '\hline'
        print '1, 0 & 1, 1 & 1, 2 \\\\'
        print '\hline'
        print '\end{tabular}'
        print '\end{table*}'

