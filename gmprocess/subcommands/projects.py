import os
import sys
import logging
import shutil
import yaml
import pkg_resources

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.utils.prompt import \
    query_yes_no, set_project_paths, get_default_project_paths
from gmprocess.utils.constants import CONFIG_FILE_PRODUCTION


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
            'default': None
        }, {
            'short_flag': '-c',
            'long_flag': '--create',
            'help': 'Create a project and switch to it.',
            'action': 'store_true',
            'default': False
        }, {
            'short_flag': '-d',
            'long_flag': '--delete',
            'help': 'Delete existing project PROJECT.',
            'type': str,
            'metavar': 'PROJECT',
            'default': None
        },
    ]

    def main(self, gmp):
        """
        Manage gmp projects.

        Args:
            gmp:
                GmpApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)
        args = gmp.args
        config = gmp.projects_conf
        configfile = gmp.PROJECTS_FILE

        if gmp.args.create:
            create(config)
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
            sp = Project(newproject, config['projects'][newproject],
                         is_current=True)
            print('\nSwitched to project: \n%s\n' % (str(sp)))
            sys.exit(0)

        if args.delete:
            project = args.delete
            if project not in config['projects']:
                msg = ('Project %s not in %s.  Run \'%s\' -l to available '
                       'projects.')
                print(msg % (project, configfile, self.command_name))
                sys.exit(1)

            conf_path = config['projects'][project]['conf_path']
            data_path = config['projects'][project]['data_path']

            question = ('Are you sure you want to delete everything in:\n'
                        '%s\n--and--\n%s?\n' % (conf_path, data_path))
            if not query_yes_no(question, default='yes'):
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
    def __init__(self, name, indict, is_current=False):
        self.name = name
        self.conf_path = indict['conf_path']
        self.data_path = indict['data_path']
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


def create(config):
    """
    Args:
        config (ConfigObj):
            ConfigObj instance representing the parsed projects config.
        project (str):
            Project name.
    """
    project = input('Please enter a project title: ')
    if 'projects' in config and project in config['projects']:
        msg = ('Project %s already in %s.  Run \'projects -l\' to see '
               'available projects.')
        print(msg % (project, config))
        sys.exit(1)
    default_conf, default_data = get_default_project_paths(project)
    new_conf_path, new_data_path = \
        set_project_paths(default_conf, default_data)

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

    # Sart with production conf from repository, then add user info
    data_path = pkg_resources.resource_filename('gmprocess', 'data')
    current_conf = os.path.join(data_path, CONFIG_FILE_PRODUCTION)
    print('reading %s' % current_conf)
    with open(current_conf, 'rt', encoding='cp850') as f:
        gmp_conf = yaml.load(f, Loader=yaml.SafeLoader)

    print('Please enter your name and email. This informaitn will be added '
          'to the config file and reported in the provenance of the data '
          'processed in this project.')
    user_info = {}
    user_info['name'] = input('\tName: ')
    user_info['email'] = input('\tEmail: ')
    gmp_conf['user'] = user_info
    proj_conf_file = os.path.join(new_conf_path, 'config.yml')
    with open(proj_conf_file, 'w') as yf:
        yaml.dump(gmp_conf, yf, Dumper=yaml.SafeDumper)
