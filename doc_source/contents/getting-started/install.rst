Installation
============


Installing from source (Mac and Linux)
--------------------------------------

.. admonition:: Prerequisites

   - A C compiler. On a mac, this usually means installing XCode/Comomand Line
     tools. For linux, it depends on the variate but is usually very stright
     forward.
   - Bash shell, curl, and git.

First clone this repository and go into the root directory with

.. code-block::

   git clone https://github.com/usgs/groundmotion-processing.git
   cd groundmotion-processing


The ``install.sh`` script in the root directory of the package installs this 
package and all other dependencies, including python and the required python 
libraries. It is regularly tested on OSX and Linux systems.

.. code-block::

   bash install.sh

Installing from source (Windows)
--------------------------------------

Our development team is not proficient with Windows systems, so our ability to 
support Windows installs is limited. But we know that the code compiles and 
passes tests in Windows on our continuous integration systems. We have also 
helped users install the code using the following steps.

.. admonition:: Prerequisites

   - A C compiler. We have had success follwing these 
     `instructions <https://github.com/cython/cython/wiki/CythonExtensionsOnWindows#using-windows-sdk-cc-compiler-works-for-all-python-versions>`_
     from cython.
   - Git and some kind of console.

First clone this repository and go into the root directory with

.. code-block::

   git clone https://github.com/usgs/groundmotion-processing.git
   cd groundmotion-processing

Then install the ``gmprocess`` virtual environment and all of the dependencies
and activate the environment

.. code-block::

   conda create --name gmprocess  python=3.8 --file requirements.txt --strict-channel-priority -c conda-forge -y -v
   call activate gmprocess

Also, we need to install OpenQuake via pip rather than conda:

.. code-block::
   
   pip install --upgrade --no-dependencies https://github.com/gem/oq-engine/archive/engine-3.12.zip

And install the gmprocess code in the ``gmprocess`` virtual environment

.. code-block::

   pip install -e . --no-deps --force-reinstall

Installing via conda
--------------------

The conda package is the easiest way to install the code but it is difficult
to keep it up to date. This is why we recommend installing from source as
described above at this time.

.. code-block::

   conda create -n gmprocess gmprocess

See the 
`conda docs <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_ 
for additional details on managing conda virtual environments.



Tests
-----

In the root directory of this repositry, you can run our unit tests with 
``pytest``:

.. code-block::

   py.test .


This will be followed by a lot of terminal output. Warnings are expected to 
occur and do not indicate a problem. Errors indicate that something has gone
wrong.

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
