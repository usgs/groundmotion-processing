
import os
import time
from shutil import which

from obspy.core.utcdatetime import UTCDateTime

from impactutils.io.cmd import get_command_output
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
\\includegraphics[height=15cm]
    {[PLOTPATH]}

"""

BEGIN_COL = """\\begin{minipage}[t]{0.3\\textwidth} \\tiny \\centering"""

END_COL = """\\end{minipage}"""


def build_report(sc, directory, origin):
    """
    Build latex summary report.

    Args:
        st (StreamCollection):
            StreamCollection of data.
        directory (str):
            Directory for saving report.

    """
    # Need to get config to know where the plots are located
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

        for i, tr in enumerate(st):
            # Disallow more than three columns
            if i > 2:
                break
            prov_latex = get_prov_latex(tr)
            report += BEGIN_COL
            report += prov_latex
            if tr.hasParameter('failure'):
                report += '\n' + tr.getParameter('failure')['reason']
            report += END_COL
            if i < len(st):
                report += '\\hspace{1em}'

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


def get_prov_latex(tr):
    """
    Construct a latex representation of a trace's provenance.

    Args:
        prov (StationTrace):
            StationTrace of data.

    Returns:
        str: Latex tabular representation of provenance.
    """
    # Table will have 3 columns: prov_id, prov_attribute, prov_attribute value
    TAB_TOP = """
    %s
    \\begin{tabular}{lll}
    \\toprule
    """ % tr.get_id()
    ONE_ROW = """
    %s & %s & %s \\\\
    """
    TAB_BOT = """
    \\bottomrule
    \\end{tabular}
    """
    all_prov = tr.getAllProvenance()
    prov_string = TAB_TOP
    for prov in all_prov:
        prov_id = str_for_latex(prov['prov_id'])
        for i, (k, v) in enumerate(prov['prov_attributes'].items()):
            if isinstance(k, str):
                kl = str_for_latex(k)
            elif isinstance(k, UTCDateTime):
                kl = k.timestamp
            else:
                kl = k

            if isinstance(v, str):
                vl = str_for_latex(v)
            elif isinstance(v, UTCDateTime):
                vl = v.timestamp
            else:
                vl = v

            if i == 0:
                vals = (prov_id, kl, vl)
            else:
                vals = ('', kl, vl)
            prov_string += ONE_ROW % vals

    prov_string += TAB_BOT

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
