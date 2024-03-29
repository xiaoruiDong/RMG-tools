#!/usr/bin/env python3
"""
The toolbox for common tasks
"""

import logging
import os
import re
import yaml

from rmgpy.species import Species

##################################################################

def read_yaml_file(path):
    """A handy function for reading yaml files"""
    with open(path, 'r') as f:     
        content = yaml.load(stream=f, Loader=yaml.FullLoader)
    return content


def write_yaml_file(path, data):
    """A handy function for writing yaml files"""
    content = yaml.dump(data=data)
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path) and dir_path:
        os.makedirs(os.path.dirname(path))
    with open(path, 'w+') as f:
        f.write(content)


def string_representer(dumper, data):
    """Add a custom string representer to use block literals for multiline strings"""
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar(tag='tag:yaml.org,2002:str', value=data, style='|')
    return dumper.represent_scalar(tag='tag:yaml.org,2002:str', value=data)


def unicode_representer(dumper, data):
    """Add a custom unicode representer to use block literals for multiline strings"""
    if len(data.splitlines()) > 1:
        return yaml.ScalarNode(tag='tag:yaml.org,2002:str', value=data, style='|')
    return yaml.ScalarNode(tag='tag:yaml.org,2002:str', value=data)


def find_blocks(f, head_pat, tail_pat, regex=True, tail_count=1, block_count=1):
    """
    Return lists of blocks between two regular expressions.

    Args:
        f (fileObject): A python fileObject
        head_pat (str/regex): Str pattern or regular expression of the head of the block
        tail_pat (str/regex): Str pattern or regular expresion of the tail of the block
        regex (bool): Whether to use regex to search
        tail_count (int): The number of time that the tail repeats
        block_count (int): The number of the blocks to search

    Return:
        blk_ps (list): List of paired indices indicating the begining
                       and the ending of the blocks
    """
    blk_ps = []
    # Different search mode
    if regex:
        search = lambda x, y: re.search(x, y)
    else:
        search = lambda x, y: x in y
    # 'search' for the head or 'read' until the tail
    mode = 'search'
    line = f.readline()
    while line != '':
        if mode == 'search':
            if (len(blk_ps)) == block_count:
                break
            else:
                match = search(head_pat, line)
                if match:
                    count = 0
                    mode = 'read'
                    blk_ps.append([f.tell(), ])
        elif mode == 'read':
                match = search(tail_pat, line)
                if match:
                    count += 1
                    if count == tail_count:
                        blk_ps[-1].append(last_line)
                        mode = 'search'
                else:
                    last_line = f.tell()
        line = f.readline()
    # Remove the last incomplete search
    if len(blk_ps) > 0 and len(blk_ps[-1]) == 1:
        blk_ps.pop()
    return blk_ps


def get_files_by_regex(file_path, regex):
    """
    Get all the file paths corresponding the regex given

    Args:
        file_path (str): The directory which contains files to be found
        regex (regex): The regular expression of the search

    Return:
        file_list (list): A list of file paths
    """
    file_list = list()
    for root, _, files in os.walk(file_path):
        for file_name in files:
            if re.search(regex, file_name):
                file_list.append(os.path.join(root, file_name))
    return file_list


def read_block(f, start=0, end=0, action=None):
    """
    Read the blocks and conduct assigned action from start to end

    Args:
        f (fileObject): A python fileObject
        start (int): Start postion at the file object
        end (int): End position at the file object
        action (function): A function takes line as input

    Returns:
        lines (list): Lines between start and end. Only available
                      when action is not assigned. 
    """
    # If end not assigned, then change it to the end of the file
    if not end:
        f.seek(0, 2)
        end = f.tell()
    # If not action, then just return the corresponding lines
    lines = []
    if not action:
        action = lambda line: lines.append(line)

    # From start til end, perform action to each line
    f.seek(start)
    line = f.readline()
    while f.tell() <= end and line != '':
        action(line)
        line = f.readline()

    if lines:
        return lines


def get_files_by_suffixes(file_path, suffixes):
    """
    Get all the file paths corresponding the suffixes given

    Args:
        file_path (str): The directory which contains files to be found
        suffixes (list): A list of file suffixes in str

    Returns:
        file_list (list): A list of file paths
    """
    file_list = list()
    for root, _, files in os.walk(file_path):
        for file_name in files:
            for suffix in suffixes:
                regex = r'\S*' + suffix + '$'
                match = re.match(regex, file_name)
                if match:
                    file_list.append(os.path.join(root, file_name))
                    break
    return file_list
