#!/usr/bin/env python 
#-*- coding: utf-8 -*-

import os, getpass, sys
import toml
from pathlib import Path
from logging.config import dictConfig
from typing import List
import collections.abc


# Affects config directories etc
APPLICATION_NAME = "streamviewer"

# Do not change here, just use an override instead
DEFAULT_CONFIG = """
[application]
page_title="stream"
hls_path="/data/hls"
"""

# Config for the logger, there should be no need to make
# manual changes here
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


def this_or_else(this: str, other: str) -> str:
    """
    Return this appended with the application name
    if this is a non-empty string otherwise return other
    """
    if this is None or this.strip() == "":
        return other
    else:
        return "{}/{}".format(this, APPLICATION_NAME)


def get_home() -> str:
    """
    Get the home directory from the environment variable
    """
    return os.environ.get("HOME")


def get_config_directories() -> List[dict]:
    """
    Returns a list of potential directories where the config could be stored.
    Existence of the directories is _not_ checked
    """

    # Generate a etc directory (usually /etc/stechuhr-server)
    etc_directory = "/etc/{}".format(APPLICATION_NAME)

    # Get the default config dir (usually /home/user/.config/stechuhr-server)
    default_config_home = "{}/.config/{}".format(get_home(), APPLICATION_NAME)

    # Unless the XDG_CONFIG_HOME environment variable has been set, then use this instead
    default_config_home = this_or_else(os.environ.get("XDG_CONFIG_HOME"), default_config_home)

    # Create the list of directories
    config_directories = [
        { "path": Path(etc_directory), "kind": "default", "source": None },
        { "path": Path(default_config_home), "kind": "default", "source": None }
    ]

    # If the STECHUHR_SERVER_CONFIG_PATH environment variable exists append to list
    key = "{}_CONFIG_DIR".format(APPLICATION_NAME.upper()).replace("-", "_").replace(" ", "_")
    if os.getenv(key) is not None:
        env_dir = { "path": Path(os.getenv(key)), "kind": "env", "source": key }
        config_directories.append(env_dir)

    return config_directories

def get_potential_config_file_paths() -> List[dict]:
    """
    Returns a list of config file paths in reverse order of importance
    (last overrides first, non-existing paths may be contained)
    """

    config_paths = []

    for directory in get_config_directories():
        for path in sorted(directory["path"].glob('*.toml')):
            path = { "path": path, "kind": "default", "source": None }
            config_paths.append(path)

    # If the STECHUHR_SERVER_CONFIG_PATH environment variable exists append to list
    key = "{}_CONFIG_PATH".format(APPLICATION_NAME.upper()).replace("-", "_").replace(" ", "_")
    if os.getenv(key) is not None:
        env_path = { "path": Path(os.getenv(key)), "kind": "env", "source": key }
        config_paths.append(env_path)

    # Add information about a paths existence
    for p in config_paths:
        p["exists"] = p["path"].is_file()

    return config_paths

def get_existing_config_file_paths() -> List[Path]:
    """
    Returns a list of existing config file paths in reverse order of importance
    (last overrides first)
    """

    return [p["path"] for p in get_potential_config_file_paths() if p["path"].is_file()]

def has_no_existing_config() -> bool:
    """
    Returns true if there is no existing config
    """
    return len(get_existing_config_file_paths()) == 0


def merge(this: dict, that: dict) -> dict:
    """
    Merge dict this in to dict that
    """
    for key, value in that.items():
        if isinstance(value, collections.abc.Mapping):
            this[key] = merge(this.get(key, {}), value)
        else:
            this[key] = value
    return this


def initialize_config(logger=None) -> dict:
    """
    Initialize a configuration. If none exists, create a default one
    """
    config = toml.loads(DEFAULT_CONFIG)

    # Return if there is no other config
    if has_no_existing_config():
        if logger is not None:
            logger.warning("Using default configuration, create an override by running config create")
        else:
            print("Using default configuration, create an override by running config create")
        return config

    if logger is not None:
        logger.info("Reading Configs in this order:")
        logger.info("Config [1]: DEFAULT_CONFIG (hardcoded)")
    else:
        print("Reading Configs in this order:")
        print("Config [1]: DEFAULT_CONFIG (hardcoded)")

    # Read all existing configs in order and merge/override the default one
    for i, p in enumerate(get_existing_config_file_paths()):
        next_config = read_config(p)
        config = merge(config, next_config)
        if logger is not None:
            logger.info("Config [{}]: {} (overrides previous configs)".format(i+2, p))
        else:
            print("Config [{}]: {} (overrides previous configs)".format(i+2, p))

    return config


def read_config(config_path: str) -> dict:
    """
    Read a config.toml from the given path,
    return a dict containing the config
    """
    with open(str(config_path), "r", encoding="utf-8") as f:
        config = toml.load(f)
    return config


def main():
    """
    Gets run only if config.py is called directly or via `poetry run config`
    Entry point for the CLI application
    """

    # List of available commands and their respective functions
    commands = {
        "default" : print_default,
        "paths": print_paths,
        "directories": print_directories,
        "create": create_config,
        "test": test
    }

    # List of available options
    availaible_options = [
        ["-h", "--help"]
    ]

    # If no argument has been passed display the help and exit
    if len(sys.argv) == 1:
        print_help()
        exit()

    # Extract the command arguments
    command_args = [c for c in sys.argv[1:] if not c.strip().startswith("-")]

    # Extract the short_options
    short_options = [c.lstrip("-") for c in sys.argv[1:] if c.strip().startswith("-") and not c.strip().startswith("--")]

    # Flatten the short_options to e.g. so -1234 will result in ["1", "2", "3", "4"]
    short_options = [item for sublist in short_options for item in sublist]

    # Extract the long options
    long_options = [c.lstrip("--") for c in sys.argv[1:] if c.strip().startswith("--")]

    errored = False
    # Short Options
    for o in short_options:
        if o not in [a[0].lstrip("-") for a in availaible_options]:
            print("Error: the option \"-{}\" does not exist.".format(o), file=sys.stderr)
            errored = True

    # Long Options
    for o in long_options:
        if o not in [a[0].lstrip("--") for a in availaible_options]:
            print("Error: the option \"--{}\" does not exist.".format(o), file=sys.stderr)
            errored = True

    # If any of the above errored, exit. This allows to display all errors at once
    if errored:
        print("\nCheck the available commands and options below:")
        print()
        print_help()
        exit()

    # Currently we only handle a single command
    if len(command_args) == 1:
        command = sys.argv[1]
        # Short commands are allowed if they are not ambigous. E.g "te" will trigger "test"
        if not any([c.startswith(command.strip().lower()) for c in commands.keys()]):
            # No fitting command has been found, print helpt and exit
            print_help()
            exit()
        elif len([c for c in commands.keys() if c.startswith(command.strip().lower())]) > 1:
            # More than one fitting command has been found, display this message
            print("Ambiguous Input: There are {} commands starting with \"{}\": {}".format(
                len([c for c in commands.keys() if c.startswith(command.strip().lower())]),
                command,
                ", ".join([c for c in commands.keys() if c.startswith(command.strip().lower())])
            ))
        else:
            # A command has been found:
            choice = [c for c in commands.keys() if c.startswith(command.strip().lower())][0]

            # If there is a -h or --help option, display the function's docstring
            # otherwise execute the function
            if "h" in short_options or "help" in long_options:
                print("Help: config {}".format(commands[choice].__name__))
                print(commands[choice].__doc__)
            else:
                commands[choice]()
    else:
        # If more than one command is given, display the help
        print_help()


def test():
    """
    Reads all configs like it would in production, prints out the order in which the config files are read and spits out the final resulting toml config
    """
    import pprint
    config = initialize_config()
    print("\nvvvvvvvvvvvvv Below is the resulting config vvvvvvvvvvvvv\n")
    print(toml.dumps(config))

def print_default():
    """
    Prints the default config.toml
    """
    print(DEFAULT_CONFIG)


def print_paths():
    """
    Prints the potential paths where a config could or should be. If environment variables are used to specify said path, this will be mentioned. If a file doesn't exist, it will be mentioned as well.
    """
    paths = get_potential_config_file_paths()
    if paths is not None:
        for p in paths:
            if p["kind"] == "env":
                if p["exists"]:
                    print("{} (set by environment variable {})".format(p["path"], p["source"]))
                else:
                    print("{} (set by environment variable {}, but doesn't exist)".format(p["path"], p["source"]))
            else:
                if p["exists"]:
                    print("{}".format(p["path"]))
                else:
                    print("{} (doesn't exist yet)".format(p["path"]))
    else:
        print("There are no paths..")


def print_directories():
    """
    Prints a list of directories where configs are searched for.
    Lower directories override higher directories.
    """
    directories = get_config_directories()
    if directories is not None:
        for d in directories:
            if d["kind"] == "env":
                print("{} (set by environment variable {})".format(d["path"], d["source"]))
            else:
                print("{}".format(d["path"]))
    else:
        print("There are no directories..")


def create_config():
    """
    Interactivally create a config directory at a choice of different places with a default config in it.
    """
    helptext = """Configs are read from the following directories (later overrides earlier):
1. DEFAULT_CONFIG (use config default to inspect)
2. /etc/stechuhr-server/*.toml (in alphabetical order)
3. $XDG_CONFIG_HOME/stechuhr-server/*.toml (in alphabetical order)
4. $STECHUHR_SERVER_CONFIG_DIR/*.toml (in alphabetical order)
5. $STECHUHR_SERVER_CONFIG_PATH (final override)
"""
    print(helptext)
    print()
    print("Select one of the following options to create a new config:")
    config_directories = get_config_directories()
    for i, p in enumerate(config_directories):
        # Create a source string describing the origin of the directory
        if p["kind"] == "env":
            source = "set via environment variable {}, ".format(p["source"])
        else:
            source = ""
        # Display some options
        if p["path"].is_dir():
            config_path = Path("{}/{}".format(p, "00-config.toml"))
            if not config_path.is_file():
                print("  [{}] {} ({}create 00-config.toml there)".format(i, p["path"], source))
            else:
                print("  [{}] {} ({}override existing 00-config.toml!)".format(i, p["path"], source))
        elif p["path"].is_file():
            pass
        else:
            print("  [{}] {} ({}dir doesn't exist: create, then write 00-config.toml there)".format(i, p["path"], source))
    print("  [x] Do nothing")
    print()

    # Collect the selection input
    selection = None
    while selection is None or not selection in [str(i) for i, p in enumerate(config_directories)]:
        selection = input("Select one of the above: ")
        if selection.lower() in ["x"]:
            break

    # If nothing has been selected, exit
    if selection.lower() == "x":
        exit()

    # Store the selected directory here
    selection = config_directories[int(selection)]

    # Create the directory if it doesn't exist yet
    selection.mkdir(mode=0o755, parents=True, exist_ok=True)
    config_path = Path("{}/{}".format(selection, "00-config.toml"))

    # If the 00-config.toml already exists, ask whether it shall be moved to 00-config.toml.old
    if config_path.is_file():
        # Create an alternate config path, incrementing up if .old already exists
        alt_config_path = None
        i = 1
        while alt_config_path is None or alt_config_path.exists():
            if i == 1:
                alt_config_path = Path("{}.old".format(config_path))
            else:
                alt_config_path = Path("{}.old{}".format(config_path, i))
            i += 1

        # Ask for confirmation
        confirmation = None
        while confirmation is None or not confirmation.lower().strip() in ["y", "n"]:
            confirmation = input("Move existing file at \"{}\" to \"{}\"? [Y/n]:\t".format(config_path, alt_config_path))
        if confirmation.lower().strip() != "y":
            exit()
        else:
            config_path.rename(alt_config_path)
            print("Moved existing file \"{}\" to \"{}\"".format(config_path, alt_config_path))

    # Create the config.toml or display a hint if the permissions don't suffice
    try:
        config_path.write_text(DEFAULT_CONFIG)
    except PermissionError as e:
        print()
        print("Error: Didn't have the permissions to write the file to {}".format(config_path), file=sys.stderr)
        print("       Directory \"{}\" belongs to user {} (was running as user {})".format(selection, selection.owner(), getpass.getuser()), file=sys.stderr)
        print()
        print("Hint:  Change the owner of the directory temporarily to {} or run {} config create with more permissions".format(getpass.getuser(), APPLICATION_NAME))
        exit()
    print("Default Config has been written to {}".format(config_path))


def print_help():
    """
    Print the help
    """
    helptext = """========= {} CONFIG =========

Helper tool for managing and installing a stechuhr-server config.

Configs are read from the following directories (later overrides earlier):
1. DEFAULT_CONFIG (see below)
2. /etc/stechuhr-server/*.toml (in alphabetical order)
3. $XDG_CONFIG_HOME/stechuhr-server/*.toml (in alphabetical order)
4. $STECHUHR_SERVER_CONFIG_DIR/*.toml (in alphabetical order)
5. $STECHUHR_SERVER_CONFIG_PATH (final override)

Commands:
    create  . . . . . Interactivly create a default config file
    default . . . . . Prints default config.toml to stdout
    directories . . . Prints which config directories are read
    paths . . . . . . Prints which config files are read
    test  . . . . . . Read in the configs and print the resulting combined toml

Options:
    -h, --help  . . . Display the help message of a command
    """.format(APPLICATION_NAME.upper())

    print(helptext)


if __name__ == "__main__":
    main()