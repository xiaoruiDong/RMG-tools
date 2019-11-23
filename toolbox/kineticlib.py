#!/usr/bin/env python3
"""
The toolbox for kinetic library related tasks
"""

import logging
import os

from rmgpy import settings
from rmgpy.chemkin import load_chemkin_file
from rmgpy.data.base import Entry
from rmgpy.data.kinetics import KineticsLibrary
from rmgpy.data.thermo import ThermoLibrary

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
