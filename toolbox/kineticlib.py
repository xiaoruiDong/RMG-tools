#!/usr/bin/env python3
"""
The toolbox for kinetic library related tasks
"""

import logging
import os
from collections import OrderedDict
from copy import deepcopy

from rmgpy import settings
from rmgpy.chemkin import load_chemkin_file
from rmgpy.data.base import Entry
from rmgpy.data.kinetics import KineticsLibrary
from rmgpy.data.kinetics.database import KineticsDatabase

from toolbox.reaction import get_kinetic_data

##################################################################


def chemkin_to_kinetic_lib(chem_path, dict_path, name, save_path='', use_chemkin_names=True):
    """
    Convert a CHEMKIN file into a RMG kinetic library given species dictionary
    and the library name.

    Args:
        chem_path (str): The path to the CHEMKIN file
        dict_path (str): The path to a species dictionary
        name (str): The name of the new library
        save_path (str): The path to the saving directory. By default, the library
                         will be saved to RMG-database repository
        use_chemkin_names (bool): Use the original CHEMKIN species name
    """
    # Load the reactions from the CHEMKIN FILE
    logging.info('Loading CHEMKIN file %s with species dictionary %s'
                 %(chem_path, dict_path))
    _, rxns = load_chemkin_file(chem_path, dict_path,
                                    use_chemkin_names=use_chemkin_names)
    kinetic_lib = KineticsLibrary(name=name)
    kinetic_lib.entries = {}
    # Create new entries
    for i in range(len(rxns)):
        rxn = rxns[i]
        entry = Entry(
            index=i + 1,
            label=str(rxn),
            item=rxn,
            data=rxn.kinetics,
        )
        try:
            entry.long_desc = 'Originally from reaction library: ' + \
                rxn.library + "\n" + rxn.kinetics.comment
        except AttributeError:
            entry.long_desc = rxn.kinetics.comment
        kinetic_lib.entries[i + 1] = entry
        logging.info('Adding reaction %s in to the kinetic library %s' %(entry.label, name))
    # Check for duplicates and convert them to multiArrhenius / multiPdepArrehenius
    kinetic_lib.check_for_duplicates(mark_duplicates=True)
    kinetic_lib.convert_duplicates_to_multi()
    # Save the library
    if not save_path:
        save_path = os.path.join(settings['database.directory'], 'kinetics',
                                 'libraries')
    try:
        os.makedirs(os.path.join(save_path, name))
    except:
        pass
    logging.info('Saving the kinetic library to %s' %(os.path.join(save_path, name)))
    kinetic_lib.save(os.path.join(save_path, name, 'reactions.py'))
    kinetic_lib.save_dictionary(os.path.join(save_path, name, 'dictionary.txt'))


def read_kinetic_lib_from_path(lib_path, kinetic_db, overwrite=False, create=False):
    """
    Read RMG kinetic library given its file path. The species dictionary should
    be included under the same directory.

    Args:
        lib_path (str): Path to thermo library file
        kinetic_db (RMG KineticsDatabase): RMG  database object
    """
    if not os.path.exists(lib_path) and create:
        create_kinetic_lib(os.path.dirname(lib_path))
        lib = KineticsLibrary()
        kinetic_db.libraries[lib_path] = lib
        kinetic_db.library_order.append(lib_path)
        logging.info('Created kinetics library {1} at {0} ...'.format(
            os.path.split(lib_path)[0], os.path.split(lib_path)[1]),)
    elif lib_path not in kinetic_db.library_order or overwrite:
        lib = KineticsLibrary()
        try:
            lib.load(lib_path, KineticsDatabase().local_context,
                     KineticsDatabase().global_context)
        except:
            logging.error('The library file %s is not vaild.' % (lib_path))
        else:
            lib.label = lib_path
            kinetic_db.libraries[lib.label] = lib
            kinetic_db.library_order.append(lib.label)
            logging.info('Loading kinetics library {1} from {0} ...'.format(
                os.path.split(lib_path)[0], os.path.split(lib_path)[1]),)
    else:
        logging.warning('The library %s has already been loaded' % (lib_path))


def create_kinetic_lib(path):
    """
    Create an empty kinetic library and an empty species dictionary according to the path

    Args:
        path (str): The non-existing file path to create kinetic libraries and species dictionary
    """
    lib_path = os.path.join(path, 'reactions.py')
    if os.path.isfile(lib_path):
        logging.warn('File %s is already existed, not overwriting.' %(lib_path))
    # Create an empty kinetics library file
    lib = KineticsLibrary()
    lib.save(lib_path)
    dict_path = os.path.join(path, 'dictionary.txt')
    with open(dict_path, 'w+'):
        pass

def create_kinetics_entry(label, rxn, index, k_data, settings):
    """
    Create a kinetic library entry given its label, corresponding reaction,
    kinetic parameters, settings, and the library instance

    Args:
        label (str): The reaction label
        rxn (RMG Reaction): The corresponding RMG reaction instance
        index (int): The index of the new entry
        k_data (dict): A dictionary contains the information about
                        A factor, n, Ea, T0 and multiplier
        settings (dict): A dictionary contains the information about
                         variable units, T and P range, description
    Returns:
        entry (RMG Entry): The created RMG kinetic entry
    """
    entry = Entry()
    entry.index = index
    entry.label = label
    entry.item = rxn
    data = get_kinetic_data(k_data, settings)
    entry.data = data
    short_desc = ''
    if 'level_of_theory' in settings and settings['level_of_theory']:
        short_desc += 'calculated at {}'.format(settings['level_of_theory'])
    if 'experiment' in settings and settings['experiment']:
        short_desc += settings['experiment']
    if 'literature_index' in settings and settings['literature_index']:
        short_desc += ' from [{}]'.format(settings['literature_index'])
    if 'compute_by' in settings and settings['compute_by']:
        short_desc += ' by {}'.format(settings['compute_by'])
    entry.short_desc = short_desc
    return entry


def remove_kinetic_entries_from_lib(label_list, library):
    """
    Remove entries from a RMG kinetics library given a list of reaction label

    Args:
        label_list (str): A list of reaction labels indicating the kinetic
                          entries to be removed
        library (RMG KineticsLibrary): The library to be removed from
    """
    new_entries = OrderedDict()
    for entry in library.entries.values():
        if entry.label not in label_list:
            index = len(new_entries)
            new_entries[index] = deepcopy(entry)
            new_entries[index].index = index
        else:
            logging.warn('Removing entry {0}'.format(entry.item))
        library.entries = new_entries
