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


def parse_gauss_scan_info(file_path, output=True):
    """
    Parse the scan info from the Gaussian output

    Args:
        file_path (str): The full path of the file
        output (bool): Whether it is an output file
    
    Returns:
        scan_info (dict): A dict contains the scan atomic indexes,
                          freeze atomic indexes, step and step size
    """
    # Parse the gaussian scan info from an output file
    if output:
        with open(file_path, 'r') as f:
            start, end = find_blocks(
                f, r'The following ModRedundant input section has been read:', r'^\s$')[0]
            scan_blk = read_block(f, start, end)
    # Parse from the gaussian input file, to be developed
    else:
        logging.error('Currently, only gaussian output parsing is supported.')
        return

    scan_info = {'scan': None, 'freeze': [], 'step': None, 'step_size': None}
    scan_pat = r'[BAD]?([\s\d]+){2,4}[\s]+S[\s\d]+[\s\d.]+'
    frz_pat = r'[DBA]?([\s\d]+){3}[\s]+F'
    value_pat = r'[\d.]+'
    for line in scan_blk:
        if re.search(scan_pat, line.strip()):
            values = re.findall(value_pat, line)
            scan_len = len(values) - 2  # atom indexes + step + stepsize
            scan_info['scan'] = [int(values[i]) for i in range(scan_len)]
            scan_info['step'] = int(values[-2])
            scan_info['step_size'] = float(values[-1])
        if re.search(frz_pat, line.strip()):
            values = re.findall(value_pat, line)
            scan_info['freeze'].append([int(values[i])
                                        for i in range(len(values))])
    return scan_info


def get_gauss_job_type(setting_dict):
    """
    Check the job type according to the setting_dict

    Args:
        setting_dict (str): A dict containing setting generated
                            from parse_gauss_options
    
    Returns:
        (str): A str represents the job type
    """
    # Check if composite job currently only contains cbs-qb3
    for method in setting_dict['method']:
        if method in ['cbs-qb3', ]:
            return 'composite'
    if 'irc' in setting_dict:
        return 'irc'
    elif 'opt' in setting_dict and 'freq' in setting_dict:
        return 'opt+freq'
    elif 'freq' in setting_dict:
        return 'freq'
    elif 'opt' in setting_dict:
        for option in setting_dict['opt']:
            if option in ['addred', 'addredundant',
                          'modred', 'modredundant']:
                return 'scan'
        else:
            return 'opt'
    else:
        return 'unknown'


def get_gauss_outputs(path):
    """
    Get the gaussian output files in a directory. Ideally, they should
    be related to the same species or conformer

    Args:
        path (str): A path to the folder contains related gaussian jobs
    
    Returns:
        gauss_files (list): A list contains all the gaussian output within
                            the path assigned
    """
    file_list = get_files_by_suffixes(path, ['.out', '.log'])
    gauss_files = []
    for gauss_file in file_list:
        with open(gauss_file, 'r') as f:
            line = f.readline()
            if 'gaussian' in line.lower():
                gauss_files.append(gauss_file)
    return gauss_files


def get_gauss_termination_status(file_path):
    """
    Get the gaussian terminations status

    Args:
        file_path (str): A path to the output of a gaussian job
    
    Returns:
        (bool): True for normal termination, False otherwise
    """
    with open(file_path, 'r') as f:
        for line in f: pass
        if 'normal termination' in line.lower():
            return True
        else:
            return False

