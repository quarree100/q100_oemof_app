# -*- coding: utf-8 -*-

"""Reegis geometry tools.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import os
import logging
import configparser as cp
import sys


FILE = None
cfg = cp.RawConfigParser()
cfg.optionxform = str
_loaded = False

# Path of the package that imports this package.
importer = os.path.dirname(sys.modules['__main__'].__file__)


def get_ini_filenames(additional_paths=None):
    paths = list()
    files = list()

    paths.append(os.path.join(os.path.dirname(__file__)))
    if additional_paths is not None:
        paths.extend(additional_paths)
    paths.append(os.path.join(os.path.expanduser("~"), 'oemof/q100_ini'))

    for p in paths:
        for f in os.listdir(p):
            if f[-4:] == '.ini':
                files.append(os.path.join(p, f))
    return files


def main():
    pass


def init(files=None, paths=None):
    """Read config file(s).

    Parameters
    ----------
    files : str or list or None
        Absolute path to config file (incl. filename)
    paths : list
        List of paths where it is searched for .ini files.
    """
    if files is None:
        files = get_ini_filenames(paths)

    cfg.read(files)
    global _loaded
    _loaded = True


def get(section, key):
    """Returns the value of a given key in a given section.
    """
    if not _loaded:
        init(FILE)
    try:
        return cfg.getint(section, key)
    except ValueError:
        try:
            return cfg.getfloat(section, key)
        except ValueError:
            try:
                return cfg.getboolean(section, key)
            except ValueError:
                try:
                    value = cfg.get(section, key)
                    if value == 'None':
                        value = None
                    return value
                except ValueError:
                    logging.error(
                        "section {0} with key {1} not found in {2}".format(
                            section, key, FILE))
                    return cfg.get(section, key)


def get_list(section, parameter, sep=',', string=False):
    """Returns the values (separated by sep) of a given key in a given
    section as a list.
    """
    try:
        my_list = get(section, parameter).split(sep)
        my_list = [x.strip() for x in my_list]

    except AttributeError:
        if string is True:
            my_list = list((cfg.get(section, parameter),))
        else:
            my_list = list((get(section, parameter),))
    return my_list


def get_dict(section):
    """Returns the values of a section as dictionary
    """
    if not _loaded:
        init(FILE)
    dc = {}
    for key, value in cfg.items(section):
        dc[key] = get(section, key)
    return dc


def get_dict_list(section, string=False):
    """Returns the values of a section as dictionary
    """
    if not _loaded:
        init(FILE)
    dc = {}
    for key, value in cfg.items(section):
        dc[key] = get_list(section, key, string=string)
    return dc


def tmp_set(section, key, value):
    if not _loaded:
        init(FILE)
    return cfg.set(section, key, value)


if __name__ == "__main__":
    print(get('paths', 'package_data'))
