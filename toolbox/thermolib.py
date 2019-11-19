#!/usr/bin/env python3
"""
The ARC Tool box
"""

import glob
import logging
import os
from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np

from rmgpy.data.thermo import ThermoLibrary, ThermoDatabase
##################################################################

def find_thermo_libs(path):
    """
    This function assumes each folder under the path
    is an ARC project directory, and search for the thermo
    library based on /Project directory/output/RMG libraries/thermo/
    Args:
        path (str): The path to project directories
    Returns:
        thermo_lib_list (list): Entries of the path to thermo libraries
    """
    # Initiate the thermo lib list
    thermo_lib_list = list()
    # Walk through the dirs under path
    for root_p, dirs, _ in os.walk(path):
        if not dirs:
            continue
        # Use ARC folder organization to check thermo library
        chk_path = os.path.join(root_p, 'output', 'RMG libraries', 'thermo')
        if os.path.isdir(chk_path):
            # Find the corresponding thermo lib file
            thermo_lib = glob.glob(os.path.join(chk_path, '*.py'))[0]
            # Check the lib is valid by loading it
            if thermo_lib:
                try:
                    lib = ThermoLibrary()
                    lib.load(thermo_lib, ThermoDatabase().local_context, ThermoDatabase().global_context)
                except:
                    continue
                else:
                    thermo_lib_list.append(thermo_lib)
                    logging.info("Find thermo library at {0}".format(thermo_lib)) 
    return thermo_lib_list


def read_thermo_lib_by_path(lib_path, thermo_db):
    """
    Read thermo library given its library path
    Args:
        lib_path (str): path to thermo library file
        thermo_database (ThermoDatabase): RMG thermo database object
    """
    if os.path.exists(lib_path) and lib_path not in thermo_db.library_order:
        lib = ThermoLibrary()
        lib.load(lib_path, ThermoDatabase().local_context,
                 ThermoDatabase().global_context)
        lib.label = lib_path
        thermo_db.libraries[lib.label] = lib
        thermo_db.library_order.append(lib.label)
        logging.info('Loading thermodynamics library {1} from {0} ...'.format(
            os.path.split(lib_path)[0], os.path.split(lib_path)[1]),)


def merge_thermo_lib(base_lib, lib_to_add):
    """
    Merge one library (lib_to_add) into the base library
    base_lib (RMG thermo library): The library used as the base
    lib_to_add (RMG thermo library): The library to be added to the base library
    """
    for spc_label, spc in lib_to_add.entries.items():
        # Check the entry merging info
        if "Added to the base library {}".format(base_lib.label) in spc.short_desc \
                or "Not used in the base library {}".format(base_lib.label) in spc.short_desc:
            continue
        # Loop through the species in the base library to check duplicates
        for _, base_spc in base_lib.entries.items():
            if spc.item.is_isomorphic(base_spc.item):
                in_base = True
                break
        else:
            in_base = False
        # if the entry is not in the base library, add its complete info into the base library
        if not in_base:
            spc.index = len(base_lib.entries)
            base_lib.entries.update({spc_label: deepcopy(spc)})
            spc.short_desc += "\nAdded to the base library {}".format(
                base_lib.label)
            logging.info("The thermo of {0} is added from {1}".format(
                spc.label, lib_to_add.label))
        else:
            draw_free_energies([base_spc, spc], label=spc.label, legends=[
                "orignial", "to be added"])
            add, neglect, tbd = False, False, False
            while (not add) and (not neglect) and (not tbd):
                decision = input("add?(A)/ neglect?(N) / TBD? (T):")
                if decision.lower() in "add":
                    add = True
                elif decision.lower() in "neglect":
                    neglect = True
                elif decision.lower() in "tbd":
                    tbd = True
            if add:
                base_spc.data = deepcopy(spc.data)
                spc.short_desc += "\nAdded to the base library {}".format(
                    base_lib.label)
                logging.info("The thermo of {0} is updated according to {1}".format(
                    spc.label, lib_to_add.label))
            elif neglect:
                spc.short_desc += "Not used in the base library {}".format(
                    base_lib.label)


def draw_free_energies(entry_list, label='', T_min=300, T_max=2000, legends="", size=4):
    """
    Plot the Gibbs free energy of a common species from two different library entries
    
    """
    # Skip this step if matplotlib is not installed
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    if T_min >= T_max:
        raise 'Invalid T_min({0}) and T_max({1}) arguments'.format(
            T_min, T_max)

    T_list = np.arange(max(300, T_min), T_max, 10.0)
    Cp_list = np.zeros((T_list.shape[0], len(entry_list)))

    for i in range(T_list.shape[0]):
        try:
            for j in range(len(entry_list)):
                Cp_list[i, j] = entry_list[j].data.get_free_energy(T_list[i])
        except (ValueError, AttributeError):
            continue

    fig = plt.figure(figsize=(size, size))
    fig.suptitle('%s' % (label))
    ax = plt.subplot(1, 1, 1)
    for i in range(len(entry_list)):
        plt.plot(T_list, Cp_list[:, i] / 4.184 / 1000)
    ax.set_xlabel('Temperature [K]')
    ax.set_xlim(T_min, T_max)
    ax.set_ylabel('Gibbs free energy (kcal/mol)')
    if legends:
        plt.legend(legends)
    else:
        plt.legend([str(i) for i in range(len(entry_list))])
    plt.show()
