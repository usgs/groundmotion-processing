import os
import sys
import logging
import textwrap
import shutil

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.utils.prompt import query_yes_no


class ProjectsModule(SubcommandModule):
    """
    Manage gmp projects.
    """
    command_name = 'projects'
    aliases = ('proj', )

    arguments = [
        {
            'short_flag': '-l',
            'long_flag': '--list',
            'help': 'List all configured gmp projects.',
            'default': False,
            'action': 'store_true'
        }, {
            'short_flag': '-s',
            'long_flag': '--switch',
            'help': 'Switch from current project to PROJECT.',
            'type': str,
            'metavar': 'PROJECT',
            'default': None,
            'nargs': 1
        }, {
            'short_flag': '-c',
            'long_flag': '--create',
            'help': 'Create new project PROJECT and switch to it.',
            'type': str,
            'metavar': 'PROJECT',
            'default': None,
            'nargs': 1
        }, {
            'short_flag': '-d',
            'long_flag': '--delete',
            'help': 'Delete existing project PROJECT.',
            'type': str,
            'metavar': 'PROJECT',
            'default': None,
            'nargs': 1
        },
    ]

    def main(self, gmp):
        """
        Manage gmp projects.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running %s.' % self.command_name)
        args = gmp.args
        config = gmp.conf
        configfile = gmp.conf_file

        if gmp.args.create:
            project = gmp.args.create
            if 'projects' in config and project in config['projects']:
                msg = ('Project %s already in %s.  Run %s -l to see available '
                       'projects.')
                print(msg % (project, configfile, self.command_name))
                sys.exit(1)
            create(config, project)
            sys.exit(0)
        config = check_project_config(config)

        if args.list:
            projects = config['projects']
            current = config['project']
            for pname, pdict in projects.items():
                is_current = False
                if pname == current:
                    is_current = True
                project = Project(
                    pname, pdict, is_current=is_current)
                print('\n' + str(project) + '\n')
            sys.exit(0)

        if args.switch:
            newproject = args.switch
            if newproject not in config['projects']:
                msg = ('Project %s not in %s.  Run %s -l to see '
                       'available projects.')
                print(msg % (newproject, configfile, self.command_name))
                sys.exit(1)
            config['project'] = newproject
            config.filename = configfile
            config.write()
            sp = Project(newproject, config['profjects'][newproject],
                         is_current=True)
            print('\nSwitched to project: \n%s\n' % (str(sp)))
            sys.exit(0)

        if args.delete:
            project = args.delete
            if project not in config['projects']:
                msg = 'Project %s not in %s.  Run %s -l to available projects.'
                print(msg % (project, configfile, self.command_name))
                sys.exit(1)

            conf_path = config['projects'][project]['conf_path']
            data_path = config['project'][project]['data_path']

            question = ('Are you sure you want to delete everything in:\n'
                        '%s\n--and--\n%s?\n' % (conf_path, data_path))
            if not args.accept and not query_yes_no(
                    question, default='yes'):
                sys.exit(0)
            shutil.rmtree(conf_path, ignore_errors=True)
            shutil.rmtree(data_path, ignore_errors=True)

            del config['projects'][project]

            if config['projects'].keys() == []:
                print('No remaining projects in projects.conf')
                default = None
                newproject = 'None'
            else:
                default = config['projects'].keys()[0]
                newproject = Project(default, config['projects'][default])
            config['project'] = default

            config.filename = configfile
            config.write()
            print('Deleted project: %s' % project)
            print('\tDeleted conf directory %s:' % conf_path)
            print('\tDeleted data directory %s:' % data_path)

            print('\nSet to new project:\n')
            print(newproject)
            sys.exit(0)

        project = config['project']
        projects = config['projects']
        if project not in projects:
            msg = ('Current project %s not in %s. Edit your projects.conf '
                   'file to match the specification.')
            print(msg % (project, configfile))
            sys.exit(1)
        sproj = Project(project, projects[project],
                        is_current=True)
        print(sproj)
        sys.exit(0)


current_markers = {
    True: '**Current Project**',
    False: ''
}


class Project(object):
    def __init__(self, name, gmp, is_current=False):
        self.name = name
        self.conf_path = gmp.conf_dir
        self.data_path = gmp.data_dir
        self.current_marker = current_markers[is_current]

    def __repr__(self):
        fmt = 'Project: %s %s\n\tConf Path: %s\n\tData Path: %s'
        tpl = (self.name, self.current_marker, self.conf_path,
               self.data_path)
        return fmt % tpl


def check_project_config(config):
    """
    Validation checks on the project config. At least one project must exist
    (otherwise exit) and the paths for each project should exist, otherwise the
    project entry is removed.

    Args:
        config (ConfigObj):
            The ConfigObj instance.
    """
    # Check that at least one project exists
    if 'projects' not in config:
        logging.error('There are currently no projects. Use "gmp '
                      'projects -c <project>" to create one.')
        sys.exit(1)
    # Check that the paths for each project exist
    for project in config['projects'].keys():
        data_exists = os.path.isdir(config['projects'][project]['data_path'])
        delete_project = False
        if not data_exists:
            logging.warn('Data path for project %s does not exist.' % project)
            delete_project = True
        conf_exists = os.path.isdir(
            config['projects'][project]['conf_path'])
        if not conf_exists:
            logging.warn(
                'Install path for project %s does not exist.' % project)
            delete_project = True
        if delete_project:
            logging.warn('    Deleting project %s.' % project)
            del config['projects'][project]
            config.write()
    return config


def create(config, project):
    """
    Args:
        config (ConfigObj):
            ConfigObj instance representing the parsed config.
        project (str):
            Project name.
    """

    project_path = os.path.join(
        os.path.expanduser('~'), 'gmprocess_projects', project)
    default_conf = os.path.join(project_path, 'conf')
    default_data = os.path.join(project_path, 'data')
    print('\n'.join(textwrap.wrap(
        'You will be prompted to supply two directories for this '
        'project:')))
    print('\n   '.join(textwrap.wrap(
        ' - A *config* path, which will store the gmprocess config files.')))
    print('\n   '.join(textwrap.wrap(
        ' - A *data* path, under which will be created directories for '
        'each event processed.\n')))
    new_conf_path, conf_ok = make_dir('conf path', default_conf)
    if not conf_ok:
        print('\n'.join(textwrap.wrap(
            'Please try to find a path that can be created on this '
            'system and then try again. Exiting.')))
        sys.exit(1)
    new_data_path, data_ok = make_dir('data path', default_data)
    if not data_ok:
        print('\n'.join(textwrap.wrap(
              'Please try to find a path that can be created on this '
              'system and then try again. Exiting.')))
        shutil.rmtree(new_data_path)
        sys.exit(1)

    if 'projects' not in config:
        config['projects'] = {}
    config['projects'][project] = {
        'conf_path': new_conf_path,
        'data_path': new_data_path
    }
    config['project'] = project
    config.write()
    sproj = Project(project, config['projects'][project])
    print('\nCreated project: %s' % (sproj))


def make_dir(pathstr, default):
    max_tries = 3
    ntries = 1
    make_ok = False
    ppath = ''
    while not make_ok:
        ppath = input('Please enter the %s: [%s] ' % (pathstr, default))
        if not len(ppath.strip()):
            ppath = default
        try:
            os.makedirs(ppath, exist_ok=True)
            make_ok = True
        except OSError:
            msg = ('Cannot make directory: %s.  Please try again (%d '
                   'of %d tries).')
            print('\n'.join(textwrap.wrap(msg % (
                ppath, ntries, max_tries))))
            ntries += 1
        if ntries > max_tries:
            break
    return (ppath, make_ok)
