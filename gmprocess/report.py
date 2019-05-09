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

% Turn off default page numbers
\\usepackage{nopageno}

% Needed for table rules
\\usepackage{booktabs}

\\usepackage[english]{babel}

\\usepackage[letterpaper, portrait]{geometry}

\\geometry{
   left=0.75in,
   top=0.5in,
   total={7in,10in},
   includeheadfoot
}

\setlength\parindent{0pt}

% Use custom headers
\\usepackage{fancyhdr}
\\pagestyle{fancy}
\\fancyhf{}
\\renewcommand{\headrulewidth}{0pt}
\\chead{[CHEAD]}
\\rfoot{\\thepage}
\\lfoot{\\today}

\\begin{document}
"""

POSTAMBLE = """
\\end{document}
"""

STREAMBLOCK = """
\\includegraphics[height=6.5in]
    {[PLOTPATH]}

"""


def build_report(sc, directory, origin, config=None):
    """
    Build latex summary report.

    Args:
        st (StreamCollection):
            StreamCollection of data.
        directory (str):
            Directory for saving report.
        origin (ScalarEvent):
            ScalarEvent object.
        config (dict):
            Config dictionary.
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
    timestr = origin.time.strftime('%m/%d/%Y, %H:%M:%S')
    report = report.replace(
        '[CHEAD]', 'M%s %s, %s' % (origin.magnitude, origin.id, timestr)
    )

    # Loop over each StationStream and append it's page to the report
    # do not include more than three.
    for st in sc:
        plot_path = os.path.join(
            '..', plot_dir,
            origin.id + '_' + st.get_id() + '.png')
        SB = STREAMBLOCK.replace('[PLOTPATH]', plot_path)
        report += SB

        prov_latex = get_prov_latex(st)

        report += prov_latex
        report += '\n'
        if st[0].hasParameter('signal_split'):
            pick_method = st[0].getParameter('signal_split')['picker_type']
            report += 'Pick Method: %s\n\n' % str_for_latex(pick_method)
        if not st.passed:
            for tr in st:
                if tr.hasParameter('failure'):
                    report += ('Failure reason: %s\n\n'
                               % tr.getParameter('failure')['reason'])
                    break
        report += '\\newpage\n\n'

    # Finish the latex file
    report += POSTAMBLE

    # Do not save report if running tests
    if 'CALLED_FROM_PYTEST' not in os.environ:
        file_name = ('gmprocess_report_%s_%s.tex'
                     % (origin.id, time.strftime("%Y%m%d-%H%M%S")))
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
    prov_string = '\\scriptsize\n' + prov_string
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
