# stdlib imports
import os
import time
from shutil import which

# third party imports
import numpy as np
import pandas as pd

# local imports
from gmprocess.config import get_config

PREAMBLE = """
\\documentclass[9pt]{article}
\\usepackage{helvet}
\\renewcommand{\\familydefault}{\\sfdefault}

\\usepackage{graphicx}

% grffile allows for multiple dots in image file name
\\usepackage{grffile}

% Turn off page numbers
\\usepackage{nopageno}

% Needed for table rules
\\usepackage{booktabs}

\\usepackage[english]{babel}

\\usepackage[letterpaper, portrait]{geometry}

\\geometry{
   left=0.5in,
   top=0.5in,
}

\setlength\parindent{0pt}

\\begin{document}
"""

POSTAMBLE = """
\\end{document}
"""

STREAMBLOCK = """
\\includegraphics[height=6.5in]
    {[PLOTPATH]}

"""

BEGIN_COL = """\\begin{minipage}[t]{%s\\textwidth} \\scriptsize \\centering"""

END_COL = """\\end{minipage}"""


def build_report(sc, directory, origin, config=None):
    """
    Build latex summary report.

    Args:
        st (StreamCollection):
            StreamCollection of data.
        directory (str):
            Directory for saving report.

    """
    # Need to get config to know where the plots are located
    if config is None:
        config = get_config()
    processing_steps = config['processing']
    # World's ugliest list comprehension:
    spd = [psd for psd in processing_steps
           if list(psd.keys())[0] == 'summary_plots'][0]
    plot_dir = spd['summary_plots']['directory']

    # Check if directory exists, and if not, create it.
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Initialize report string with PREAMBLE
    report = PREAMBLE

    # Loop over each StationStream and append it's page to the report
    # do not include more than three.
    for st in sc:
        plot_path = os.path.join('..', plot_dir, st.get_id() + '.png')
        SB = STREAMBLOCK.replace('[PLOTPATH]', plot_path)
        report += SB

        prov_latex = get_prov_latex(st)

        # for i, tr in enumerate(st):
        #     # Disallow more than three columns
        #     if i > 2:
        #         break
        #     if i == 0:
        #         prov_latex = get_prov_latex(tr)
        #         report += BEGIN_COL % "0.4"
        #     else:
        #         prov_latex = get_prov_latex(tr, include_prov_id=False)
        #         report += BEGIN_COL % "0.27"
        #     report += prov_latex
        #     if tr.hasParameter('failure'):
        #         report += '\n' + tr.getParameter('failure')['reason']
        #     report += END_COL
        #     if i < len(st):
        #         report += '\\hspace{2em}'
        report += prov_latex
        if not st.passed:
            for tr in st:
                if tr.hasParameter('failure'):
                    report += '\n' + tr.getParameter('failure')['reason']
                    break
        report += '\n\\newpage\n\n'

    # Finish the latex file
    report += POSTAMBLE

    # Do not save report if running tests
    if 'CALLED_FROM_PYTEST' not in os.environ:
        file_name = ('gmprocess_report_%s_%s.tex'
                     % (origin['id'], time.strftime("%Y%m%d-%H%M%S")))
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'w') as f:
            f.write(report)

        # Can we find pdflatex?
        pdflatex_bin = which('pdflatex')
        # rc, so, se = get_command_output('%s %s' % (pdflatex_bin, file_path))
    return st


def get_prov_latex(st):
    """
    Construct a latex representation of a trace's provenance.

    Args:
        st (StationStream):
            StationStream of data.

    Returns:
        str: Latex tabular representation of provenance.
    """
    # start by sorting the channel names
    channels = [tr.stats.channel for tr in st]
    channelidx = np.argsort(channels).tolist()
    columns = ['Process Step',
               'Process Attribute']

    trace1 = st[channelidx.index(0)]
    df = pd.DataFrame(columns=columns)
    df = trace1.getProvDataFrame()
    mapper = {'Process Value': '%s Value' % trace1.stats.channel}
    df = df.rename(mapper=mapper, axis='columns')
    for i in channelidx[1:]:
        trace2 = st[i]
        trace2_frame = trace2.getProvDataFrame()
        df['%s Value' % trace2.stats.channel] = trace2_frame['Process Value']

    lastrow = None
    newdf = pd.DataFrame(columns=df.columns)
    for idx, row in df.iterrows():
        if lastrow is None:
            lastrow = row
            newdf = newdf.append(row, ignore_index=True)
            continue
        if row['Index'] == lastrow['Index']:
            row['Process Step'] = ''
        newdf = newdf.append(row, ignore_index=True)
        lastrow = row

    newdf = newdf.drop(labels='Index', axis='columns')
    prov_string = newdf.to_latex(index=False)
    prov_string = '\\scriptsize\n\\centering\n' + prov_string
    return prov_string


def str_for_latex(string):
    """
    Helper method to convert some strings that are problematic for latex.
    """
    string = string.replace('_', '\\_')
    string = string.replace('$', '\\$')
    string = string.replace('&', '\\&')
    string = string.replace('%', '\\%')
    string = string.replace('#', '\\#')
    string = string.replace('}', '\\}')
    string = string.replace('{', '\\{')
    string = string.replace('~', '\\textasciitilde ')
    string = string.replace('^', '\\textasciicircum ')
    return string
