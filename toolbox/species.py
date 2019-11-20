#!/usr/bin/env python3
"""
The toolbox for species related tasks
"""

import logging
import os

from rmgpy.species import Species

from toolbox.base import find_blocks, read_block, read_yaml_file, write_yaml_file

##################################################################

def get_spc_list_from_labels(label_list, spc_dict):
    """
    Convert a list of species labels to a list of species info according to species dictionary
    Args:
        label_list (list): a list of species label
        spc_dict (dict): a dictionary of species
    Returns:
        spc_list (list): a list of species info 
    """
    spc_list = list()
    for label in label_list:
        try:
            spc = spc_dict[label]
        except KeyError:
            logging.error('The label %s is not in the species dictionary' %(label))
            return
        else:
            if label != spc.label:
                spc.label = label
            spc_list.append(spc)
    return spc_list


def rmg_chemkin_label(chem_path):
    """
    build up two label dictionary rmg_to_chemkin and chemkin_to_rmg from the RMG
    generated CHEMKIN file 
    Args:
        chem_path (str): the path to RMG generated CHEMKIN file
    Returns:
        rmg_to_chemkin (dict): a list of species info
    """
    rmg_to_chemkin, chemkin_to_rmg = {}, {}
    def action(line): 
        chemkin_label, _, rmg_label = line.strip().split()
        rmg_to_chemkin[rmg_label] = chemkin_label
        chemkin_to_rmg[chemkin_label] = rmg_label 
    with open(chem_path, 'r') as f:
        start, end = find_blocks(f, head_pat=r'SPECIES',
                                tail_pat=r'END', regex=True)[0]
        read_block(f, action, start, end)
    return rmg_to_chemkin, chemkin_to_rmg


def combine_spc_list(spc_list1, spc_list2, same_source=True):
    """
    combine two species list used in ARC input files
    Args:
        spc_list1 (list): One of the list containing species info for ARC input files
        spc_list2 (list): The other list
        same_source (bool): If two lists are generated using the 
                            same set of chemkin file and species dictionary
    Returns:
        spc_list (list): A list contains all of the species in spc_list1 and 
                         spc_list2
    """
    # If same source, then just compare the label
    if same_source:
        spc_list = spc_list1 + spc_list2
        spc_list = list(set(spc_list))
    # If not same source, compare the structure
    else:
        spc_list = list()
        for spc in spc_list1:
            if 'smiles' in spc.keys():
                spc_list.append(Species().from_smiles(spc['smiles']))
            elif 'adjlist' in spc.keys():
                spc_list.append(Species().from_adjacency_list(spc['adjlist']))
        for spc in spc_list2:
            if 'smiles' in spc.keys():
                species = Species().from_smiles(spc['smiles'])
            elif 'adjlist' in spc.keys():
                species = Species().from_adjacency_list(spc['adjlist'])
            for species1 in spc_list:
                if species1.is_isomorphic(species):
                    break
            else:
                spc_list.append(spc)
    return spc_list


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
        logging.info('Writing the species %s into the yaml file' %
                     (d['label']))
    else:
        pass
    if 'species' in content.keys() or not content:
        content['species'] = spc_list
    else:
        content = {}
        content['species'] = spc_list
    write_yaml_file(target, content)
