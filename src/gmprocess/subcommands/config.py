#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from gmprocess.subcommands.lazy_loader import LazyLoader

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")
ws = LazyLoader("ws", globals(), "gmprocess.io.asdf.stream_workspace")
confmod = LazyLoader("confmod", globals(), "gmprocess.utils.config")
ryaml = LazyLoader("yaml", globals(), "ruamel.yaml")


class ConfigModule(base.SubcommandModule):
    """Utilities to deal with config option issues."""

    epilog = """
    Config options are specified in the yml files in the config directory for each
    project. These are read in and stored in a config object in the workspace file
    for each event when the workspace file is created by the `assemble` subcommand.

    It sometimes occurs that the config file structure needs to be updated in a way
    that is not backwards compatible. The priory purpose of this subcommand is to
    help users resolve this problem.

    Updating the config options in the workspace file can cause an inconsistency in
    that the config options will no longer match previously processed data in that
    workspace file. Thus, the provenance information should be used as the authoritative
    source for documenting the options that were used.

    Another concern is that any customization of the config options could be lost in the
    update. So it is very important that the user be sure that the project config
    options include any customizations before updating the config in the workspace
    files.

    The `save` option is included for this subcommand as a quick way to export the
    contents of the config options with the idea that this could be compared to the
    current project config file to look for any customizatized options.
    """
    command_name = "config"

    arguments = [
        {
            "short_flag": "-u",
            "long_flag": "--update",
            "help": (
                "Replace the config in the workspace files with the config."
                "in the current project."
            ),
            "default": False,
            "action": "store_true",
        },
        {
            "short_flag": "-s",
            "long_flag": "--save",
            "help": "Save the contents of the workspace config to a file.",
            "type": str,
            "default": None,
            "metavar": "filename",
        },
    ]

    def main(self, gmrecords):
        """
        Help with the config.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")
        self.gmrecords = gmrecords
        self._check_arguments()
        self._get_events()

        logging.info(f"Number of events: {len(self.events)}")

        # Grab the config from the project on the file system
        proj_config = confmod.get_config(gmrecords.conf_path)

        for event in self.events:
            event_dir = self.gmrecords.data_path / event.id
            if event_dir.exists():
                workname = event_dir / const.WORKSPACE_NAME

                if not workname.is_file():
                    logging.info(
                        f"No workspace file found for event {event.id}. "
                        "Continuing to next event."
                    )
                    continue

                # Open workspace file
                workspace = ws.StreamWorkspace.open(workname)

                # Save the workspace configs to file?
                if self.gmrecords.args.save is not None:
                    group_name = "config/config"
                    config_exists = (
                        group_name in workspace.dataset._auxiliary_data_group
                    )
                    if config_exists:
                        logging.info(f"Saving config for {event.id}.")
                        fname = Path(self.gmrecords.args.save)
                        yaml = ryaml.YAML()
                        yaml.indent(mapping=4)
                        yaml.preserve_quotes = True
                        with open(fname, "a", encoding="utf-8") as yf:
                            yf.write(f"# Path: {workname}\n")
                            yaml.dump(workspace.config, yf)
                        self.append_file("Config", fname)
                    else:
                        logging.info(f"No config in workspace for event {event.id}.")
                if self.gmrecords.args.update:
                    # Write project config to workspace
                    logging.info(f"Adding config {event.id} workspace file.")
                    workspace.addConfig(config=proj_config, force=True)
        self._summarize_files_created()
