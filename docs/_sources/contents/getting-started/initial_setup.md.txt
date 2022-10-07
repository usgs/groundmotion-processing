# Initial Setup

In order to simplify the command line interface, the `gmrecords` command makes use of "projects".
You can have many projects configured on your system, and a project can have data from many events.
A project is essentially a way to encapsulate the configuration and data directories so that they do not need to be specified as command line arguments.

There are two different types of projects:

**directory projects**
  A directory project works by checking the current working directory for a project config file that holds the data and config info.
  Thus, in order to activate the project, you have to be in that specific directory.

**system-level projects**
  A system-level project works by checking the user's home directory for a project config file that can hold many different configured projects.
  Thus, when you use a system-level project you can switch between different projects easily from any directory on your system.

:::{attention}
See the [Configuration File](../manual/config_file) section for more information on how configuration options work.
:::

When you create either type of project, you will be prompted to include your name and email.
This information is used for the data provenance.
It is often important to be able to track where data originated.
If you do not wish to share your personal information, we recommend using an institution or project name.

To create a directory project, use the gmrecords `init` subcommand in the directory where you would like to activate the project.

```term
gmrecords init
INFO 2021-11-12 20:00:32 | gmrecords.__init__: Logging level includes INFO.
INFO 2021-11-12 20:00:32 | gmrecords.__init__: PROJECTS_PATH: /Users/<username>/.gmprocess
INFO 2021-11-12 20:00:32 | init.main: Running subcommand 'init'
Please enter a project title: [default] local
Please enter your name and email. This information will be added
to the config file and reported in the provenance of the data
processed in this project.
  Name: Eric
  Email: fake@email.com

Created project: Project: local
  Conf Path: /Users/<username>/test_gmrecords/conf
  Data Path: /Users/<username>/test_gmrecords/data
```

The `projects` subcommand is used for managing system-level projects.
The arguments are

```{program-output} gmrecords projects -h
```

The [Command Line Interface](../tutorials/cli) tutorial provides an example of how to create a system-level project.

:::{note}
When creating a new project, please review the config file that is installed and adjust the options as necessary.
Some fields have place holders (e.g., `EMAIL` for the CESMD fetcher) that must be filled in by each individual.
