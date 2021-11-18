#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import glob
import os
import subprocess

# third party imports
import numpy as np
import pandas as pd

# local imports
from gmprocess.utils.config import get_config

PREAMBLE = """
\\documentclass[9pt]{extarticle}

% Allows for 9pt article class
\\usepackage{extsizes}

\\usepackage{sansmathfonts}
\\usepackage[T1]{fontenc}

\\usepackage{graphicx}
\\usepackage{tikz}

% grffile allows for multiple dots in image file name
\\usepackage{grffile}

% Turn off default page numbers
% \\usepackage{nopageno}

% Needed for table rules
\\usepackage{booktabs}

\\usepackage[english]{babel}

\\usepackage[letterpaper, portrait]{geometry}

\\geometry{
   left=0.75in,
   top=0.0in,
   total={7in,10.5in},
   includeheadfoot
}

\\setlength\\parindent{0pt}

% Use custom headers
\\usepackage{fancyhdr}
\\pagestyle{fancy}
\\fancyhf{}
\\renewcommand{\\headrulewidth}{0pt}
\\cfoot{\\thepage}
%%\\lfoot{\\today}

\\tikzstyle{box} = [
    draw=blue, fill=blue!20, thick,
    rectangle, rounded corners]

\\begin{document}
"""

POSTAMBLE = """
\\end{document}
"""

STREAMBLOCK = """
\\begin{tikzpicture}[remember picture,overlay]
   \\draw[box] (0, 0.5) rectangle (9, 1.0) node[pos=.5]
       {\\normalsize [EVENT]};
   \\draw[box] (10, 0.5) rectangle (17, 1.0) node[pos=.5]
       {\\normalsize [STATION]};
\\end{tikzpicture}

\\includegraphics[height=5.75in]
    {[PLOTPATH]}


"""

TITLEBLOCK = """
\\begin{center}

\\vfill

\\large Summary Report

\\vspace{1cm}

gmprocess

\\vspace{1cm}

Code version: [VERSION]

\\vspace{1cm}

\\today

\\vspace{1cm}

\\includegraphics[width=0.9\\textwidth]
    {[MAPPATH]}

[MOVEOUT_PAGE]

\\end{center}

\\vfill

\\newpage\n\n

"""

moveout_page_tex = '''
\\includegraphics[width=0.9\\textwidth]
    {[MOVEOUTPATH]}
'''


def build_report_latex(st_list, directory, origin, prefix='', config=None,
                       gmprocess_version='unknown'):
    """
    Build latex summary report.

    Args:
        st_list (list):
            List of streams.
        directory (str):
            Directory for saving report.
        origin (ScalarEvent):
            ScalarEvent object.
        prefix (str):
            String to prepend to report file name.
        config (dict):
            Config dictionary.
        gmprocess_version:
            gmprocess version.
    Returns:
        tuple:
            - Name of pdf or latex report file created.
            - boolean indicating whether PDF creation was successful.

    """
    # Need to get config to know where the plots are located
    if config is None:
        config = get_config()

    # Check if directory exists, and if not, create it.
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Initialize report string with PREAMBLE
    report = PREAMBLE
    timestr = origin.time.strftime('%m/%d/%Y %H:%M:%S')

    # Does the map exist?
    map_file = os.path.join(directory, 'stations_map.png')
    if os.path.isfile(map_file):
        TB = TITLEBLOCK.replace(
            '[MAPPATH]', 'stations_map.png'
        )

        TB = TB.replace(
            '[VERSION]', gmprocess_version
        )
        moveout_file = os.path.join(directory, 'moveout_plot.png')
        if os.path.isfile(moveout_file):
            TB = TB.replace('[MOVEOUT_PAGE]', moveout_page_tex)
            TB = TB.replace('[MOVEOUTPATH]', 'moveout_plot.png')
        else:
            TB = TB.replace('[MOVEOUT_PAGE]', '')
        report += TB

    # Loop over each StationStream and append it's page to the report
    # do not include more than three.

    # sort list of streams:
    st_list.sort(key=lambda x: x.id)

    for st in st_list:
        plot_path = os.path.join(
            'plots', origin.id + '_' + st.get_id() + '.png')
        SB = STREAMBLOCK.replace('[PLOTPATH]', plot_path)
        SB = SB.replace(
            '[EVENT]', 'M %s - %s - %s'
            % (origin.magnitude, str_for_latex(origin.id), timestr)
        )
        SB = SB.replace(
            '[STATION]', st.get_id()
        )
        report += SB

        prov_latex = get_prov_latex(st)

        report += prov_latex
        report += '\n'
        if st[0].hasParameter('signal_split'):
            pick_method = st[0].getParameter('signal_split')['picker_type']
            report += 'Pick Method: %s\n\n' % str_for_latex(pick_method)
        if 'nnet_qa' in st.getStreamParamKeys():
            score_lq = st.getStreamParam('nnet_qa')['score_LQ']
            score_hq = st.getStreamParam('nnet_qa')['score_HQ']
            report += ('Neural Network LQ score: %s\n\n'
                       % str_for_latex(str(score_lq)))
            report += ('Neural Network HQ score: %s\n\n'
                       % str_for_latex(str(score_hq)))
        if not st.passed:
            for tr in st:
                if tr.hasParameter('failure'):
                    report += ('Failure reason: %s\n\n' % str_for_latex(
                               tr.getParameter('failure')['reason']))
                    break
        report += '\\newpage\n\n'

    # Finish the latex file
    report += POSTAMBLE

    res = False
    # Do not save report if running tests
    if 'CALLED_FROM_PYTEST' not in os.environ:

        # Set working directory to be the event subdirectory
        current_directory = os.getcwd()
        os.chdir(directory)

        # File name relative to current location
        file_name = ('%s_report_%s.tex' % (prefix, origin.id))

        # File name for printing out later relative base directory
        latex_file = os.path.join(directory, file_name)
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(report)

        # Can we find pdflatex?
        try:
            cp = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', file_name],
                capture_output=True,
                text=True
            )
            report_file = latex_file
            if cp.returncode == 0:
                base, ext = os.path.splitext(file_name)
                pdf_file = base + '.pdf'
                if os.path.isfile(pdf_file):
                    report_file = pdf_file
                    auxfiles = glob.glob(base + '*')
                    auxfiles.remove(pdf_file)
                    for auxfile in auxfiles:
                        os.remove(auxfile)
                else:
                    res = False
            else:
                print('pdflatex output:')
                print(cp.stdout)
                print(cp.stderr)
        except BaseException:
            report_file = ''
            pass
        finally:
            os.chdir(current_directory)
    else:
        report_file = 'not run'

    # make report file an absolute path
    report_file = os.path.join(directory, report_file)

    return (report_file, res)


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
    prov_string = '\\tiny\n' + prov_string
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
