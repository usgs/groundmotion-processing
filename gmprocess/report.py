
import os
import pkg_resources
import time
from shutil import which

from gmprocess.config import get_config

PREAMBLE = """
\\documentclass[10pt]{article}
\\usepackage{helvet}
\\renewcommand{\\familydefault}{\\sfdefault}

\\usepackage{graphicx}

% grffile allows for multiple dots in image file name
\\usepackage{grffile}

\\usepackage[english]{babel}

\\usepackage[letterpaper, portrait]{geometry}

\\geometry{
   left=1in,
   top=1in,
}

\\begin{document}
\\thispagestyle{empty}
"""

POSTAMBLE = """
\\end{document}
"""

STREAMBLOCK = """
\\includegraphics[height=15cm]
    {[PLOTPATH]}
"""


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
    for st in sc:
        plot_path = os.path.join('..', plot_dir, st.get_id() + '.png')
        SB = STREAMBLOCK.replace('[PLOTPATH]', plot_path)
        report += SB

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
    return st
