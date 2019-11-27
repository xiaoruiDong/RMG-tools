#!/usr/bin/env python3
"""
The toolbox for gaussian outputs
"""

import logging
import os
import re
import yaml

import cclib
from arkane.gaussian import GaussianLog
from rmgpy.constants import Na, E_h

from toolbox.base import find_blocks, get_files_by_suffixes, read_block

##################################################################

def parse_gauss_options(file_path):
    """
    Parse the gaussian options

    Args:
        file_path (str): The full file path to the gaussian output file

    Returns:
        setting_dict (dict): A dict contains the option parameters
    """
    options = ['iop', 'opt', 'guess', 'irc',
               'scf', 'integral', 'freq', 'cbs-qb3']
    # The option example:
    # ---------------------------------------------
    # #P opt=(calcfc,ts,noeig) freq ub3lyp/6-31g(d)
    # ---------------------------------------------
    start_pat = '-' * 5
    end_pat = '-' * 5
    with open(file_path, 'r') as f:
        start, end = find_blocks(f, start_pat, end_pat,
                                 regex=False, block_count=2)[1]
        lines = read_block(f, start, end)
    settings = ''
    for line in lines:
        line = line.strip().lower()
        # Recombine setting info
        for option in options:
            # Distinguish cases like b3lyp/\ncbsb7 and opt\nscf=xqc
            if line.startswith(option):
                settings += ' '
                break
        settings += line
    # Standardize comma splits ',  ' => ',', to avoid bad splitting
    settings = re.sub(r'\,\s+', ',', settings)
    setting_dict = {}
    for option in settings.split():
        parse_gauss_option(option, setting_dict)
    return setting_dict


def parse_gauss_option(option, setting_dict):
    """
    Parse a single option of the gaussian job options

    Args:
        option (str): a single gaussian job option
        setting_dict (dict): A dict contains the option parameters
    """
    # Categorize the option
    if 'iop' in option:
        item = 'iop'
        content = option[3:]
    elif 'opt' in option:
        item = 'opt'
        if len(option) == 3:
            content = ''
        else:
            content = option[4:]
    elif 'guess' in option:
        item = 'guess'
        content = option[6:]
    elif 'irc' in option:
        item = 'irc'
        content = option[4:]
    elif 'scf' in option:
        item = 'scf'
        content = option[4:]
    elif 'integral' in option:
        item = 'integral'
        content = option[9:]
    elif 'freq' in option:
        item = 'freq'
        content = ''
    elif '/' in option:
        item = 'method'
        content = option
    elif 'cbs-qb3' in option:
        item = 'method'
        content = option
    else:
        return
    if content:
        content_list = parse_option_contents(content)
    else:
        content_list = []
    if item in setting_dict.keys():
        setting_dict[item] += content_list
    else:
        setting_dict[item] = content_list


def parse_option_contents(content):
    """
    Parse the option contents into a list

    Args:
        content (str): The content of the option

    Returns:
        content_list (list): A list contains the option parameters
    """
    content_list = []
    # Remove brackets
    bracket = re.search(r'^\((.*?)\)$', content)
    if bracket:
        content = bracket.group()[1:-1]
    # Parse each parameters
    for item in content.split(','):
        content_list.append(item.strip())
    return content_list
