Initial Setup
=============

In order to simplify the command line interface, the ``gmrecords`` command 
makes use the "projects" and you can have many projects configured on your 
system. A project is essentially a way to encapsulate the confiration and data 
directories so that they do not need to be specified as command line arguments.

There are two different types of projects:

- **directory projects** - A directory project works by checking the current
  working directory for a project config file that holds the data and config 
  info. Thus, in order to activate the project, you have to be in that specific
  directory.
- **system-level projects** - A system-level project works by checking the
  users home directory for a project config file that can hold many different
  configured projects. Thus, when you use a system-level project you can switch
  between different projects easily from any directory on your system.

When you create either type of project, you will be prompted to include your
name and email. This information is used for the data provenance. It is often
important to be able to track where data originated. If you do not which to 
share your personal information, we recommend using you institution/project 
name if possible.

To create a directory project, use the ``init`` gmrecords subcommand in the
where you would like to activate the project

.. code-block:: console

  $ gmrecords init
  INFO 2021-01-06 16:38:40 | gmrecords.__init__: Logging level includes INFO.
  INFO 2021-01-06 16:38:40 | init.main: Running subcommand 'init'

  Created project: Project: local
      Conf Path: /Users/mrmanager/test_gmrecords/conf
      Data Path: /Users/mrmanager/test_gmrecords/data
  Please enter your name and email. This informaitn will be added
  to the config file and reported in the provenance of the data
  processed in this project.
      Name: Mr Manager
      Email: mrmanager@gmrpocess.org


The ``projects`` subcommand is used for managing system-level projects. The
arguments are

.. code-block:: console

  $ gmrecords projects -h
  usage: gmrecords projects [-h] [-l] [-s PROJECT] [-c] [-d PROJECT]

  optional arguments:
    -h, --help            show this help message and exit
    -l, --list            List all configured gmrecords projects.
    -s PROJECT, --switch PROJECT
                          Switch from current project to PROJECT.
    -c, --create          Create a project and switch to it.
    -d PROJECT, --delete PROJECT
                          Delete existing project PROJECT.


Here is an example of creating a system-level project is

.. code-block:: console

  $ gmrecords projects -c
  INFO 2021-01-06 16:41:21 | gmrecords.__init__: Logging level includes INFO.
  INFO 2021-01-06 16:41:21 | projects.main: Running subcommand 'projects'
  Please enter a project title: default
  You will be prompted to supply two directories for this project:
  - A *config* path, which will store the gmprocess config files.
  - A *data* path, under which will be created directories for each
    event processed.
  Please enter the conf path: [/Users/mrmanager/gmprocess_projects/default/conf]
  Please enter the data path: [/Users/mrmanager/gmprocess_projects/default/data]

  Created project: Project: default
      Conf Path: /Users/mrmanager/gmprocess_projects/default/conf
      Data Path: /Users/mrmanager/gmprocess_projects/default/data
  Please enter your name and email. This informaitn will be added
  to the config file and reported in the provenance of the data
  processed in this project.
      Name: Mr Manager
      Email: mrmanager@gmprocess.org

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
