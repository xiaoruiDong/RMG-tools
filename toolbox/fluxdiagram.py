#!/usr/bin/env python3
"""
The ARC Tool box
"""

import logging
import os

import pydot

##################################################################

def get_spc_label_from_fluxdiagrams(file_list):
    """
    Get the list of species contained in multiple flux diagrams
    Args:
        file_list (str): a list contains the paths of flux diagram dot files    
    Return:
        spc_list (list): a list of species
    """
    # As flux diagrams under the same folder have the same species
    # we only need to read one graph
    head = len(file_list) - 1
    while len(file_list) != 0:
        if os.path.dirname(file_list[head]) == os.path.dirname(file_list[head - 1]):
            file_list.pop(head)
        head -= 1
        if head <= 0:
            break
    # get non duplicate labels from flux diagrams
    label_list = list()
    for fd in file_list:
        label_list += get_spc_label_from_fluxdiagram(fd)
    return list(set(label_list))


def get_spc_label_from_fluxdiagram(file_path):
    """
    Given the flux diagram in dot file, the species labels 
    on the flux diagram will be extracted and output as a list
    Args:
        path (str): the file path to the flux diagram dot file
    Returns:
        label_list (list): a list which contains species labels
    """
    # Read the .dot file to graph
    graph = pydot.graph_from_dot_file(file_path)
    # Extract the node list
    node_list = graph[0].get_node_list()
    # Read the name of each node which is the species label
    label_list = [node.get_name()
                for node in node_list if not node.get_name() in ["node", "graph"]]
    # Solve inconsistency in quotation marks
    # Cases that somes nodes may have extra quotation marks
    for index, label in enumerate(label_list):
        label_with_quote = label.split("\"")
        if len(label_with_quote) > 1:
            label_list[index] = label_with_quote[1]
    return label_list
