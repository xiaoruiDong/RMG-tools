#!/usr/bin/env python3
"""
The toolbox for sensitivity analysis related tasks
"""

import logging
import os

import pandas as pd
import pydot

##################################################################

def get_spc_label_from_sa(file_list, N=50, ):
    """
    Get the list of species contained in multiple sensitivity analysis
    Args:
        file_list (str): a list contains the paths of sensitivity analysis csv files
        N (int): the upperbound number of species to be extracted in each SA    
    Return:
        spc_list (list): a list of species
    """
    spc_list = list()
    for sa_file in file_list:
        max_sa = []
        df = pd.read_csv(sa_file)
        for header in df.columns:
            if 'dG' in header:
                label = header.split('dG')[1][1:-1]
                max_sa.append((label, abs(df[header]).max()))
        sorted_labels = sorted(max_sa, key=lambda tup: tup[1])
        for tup in sorted_labels[:min(len(sorted_labels), N)]:
            spc_list.append(tup[0])
        spc_list = list(set(spc_list))
    return spc_list
