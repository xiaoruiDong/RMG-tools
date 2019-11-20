#!/usr/bin/env python3
"""
The toolbox for species related task
"""

import logging
import os

from rmgpy.species import Species

from toolbox.base import find_blocks, read_block, read_yaml_file, write_yaml_file

##################################################################
def read_spc_list_from_yml(yml_file):
    """
    Read the species contained in a yaml file. The function assumes
    that species are listed under the key "species".
    It also assumes the molecule contains at least one kind of geom info.
    Currently only support SMILES and Adjacency list.
    Args:
        yml_file (str): The path to the input yml file
    Return:
        spc_list (list): A list contains all the species in the file
    """
    content = read_yaml_file(yml_file)
    if 'species' in content.keys():
        content = content['species']
    else:
        logging.error('Invalid yaml file which does not contain species entry')
        return

    spc_list = list()
    for entry in content:
        spc = Species(label=entry['label'])
        try:
            if 'adjlist' in entry.keys():
                spc.from_adjacency_list(entry['adjlist'])
            elif 'smiles' in entry.keys():
                spc.from_smiles(entry['smiles'])
        except:
            logging.warning('Species %s is not readable' % (entry['label']))
            continue
        if 'multiplicity' in entry.keys():
            spc.multiplicity = entry['multiplicity']
        spc_list.append(spc)
    return spc_list


def write_spc_list_to_yml(spc_info, yml_file, mode='backup', info_type='smiles'):
    """
    Write the species to a yaml file format. The function lists
    species under the key "species". 
    Args:
        spc_info (list): A iterable datastructure containing species info
        yml_file (str): The path to a new/existed yml file
        mode (str): 'backup' or 'overwrite'
        info_type (str): By default, it will write SMILES
    """
    exist = os.path.isfile(yml_file)
    if exist:
        try:
            content = read_yaml_file(yml_file)
        except:
            content = {}
            mode = 'backup'
            logging.warning('The yaml file is not readable, ')
    else:
        content = {}
    if not exist or mode == 'overwrite':
        target = yml_file
    else:
        target = os.path.join(os.path.dirname(yml_file),
                              'new_' + os.path.basename(yml_file))
    spc_list = list()
    if isinstance(spc_info, list):
        for entry in spc_info:
            d = {}
            if entry.label:
                d['label'] = entry.label
            else:
                d['label'] = entry.molecule[0].to_smiles().replace('#', '_')
            if info_type == 'smiles':
                d['smiles'] = entry.molecule[0].to_smiles()
            elif info_type == 'adjlist':
                d['adjlist'] = entry.to_adjacency_list()
            d['multiplicity'] = entry.multiplicity
            spc_list.append(d)
        logging.info('Writing the species %s in to the yaml file' %
                     (d['label']))
    else:
        pass
    if 'species' in content.keys() or not content:
        content['species'] = spc_list
    else:
        content = {}
        content['species'] = spc_list
    write_yaml_file(target, content)
