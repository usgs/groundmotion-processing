Installation
============

Installing via conda
--------------------

The conda package is the easiest way to install the code, but is not generally
as up to date as installing from the source code. We recommend installing 
a new conda virtual environment with

.. code-block:: console

   $ conda create -n gmprocess gmprocess


Installing from source
----------------------

First clone this repository and go into the root directory with

.. code-block:: console

   $ git clone https://github.com/usgs/groundmotion-processing.git
   $ cd groundmotion-processing


The ``install.sh`` script in the root directory of the package installs this 
package and all other dependencies, including python and the required python 
libraries. It is regularly tested on OSX, CentOS, and Ubuntu.

.. code-block:: console

   $ bash install.sh


Tests
-----

In the root directory of this repositry, you can run our unit tests with 
``pytest``:

.. code-block:: console

   $ py.test .


This will be followed by a lot of terminal output. Warnings are expected to 
occur and do not indicate a problem. Errors indicate that something has gone
wrong.

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
