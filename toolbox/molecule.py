#!/usr/bin/env python3
"""
The toolbox for molecule related tasks
"""

import logging
import os
import urllib

from rmgpy.exceptions import AtomTypeError
from rmgpy.molecule.molecule import Molecule

##################################################################

def get_molecule_from_identifier(identifier):
    """
    Get species according to the string identifier input

    Args:
        identifier (str): Identifiers used to generate species, currently 
                          support SMILES, InChI, adjacency list and common names

    Return:
        spc (RMG Species): An RMG species object corresponding to the identifier
    """
    known_names = {
        'o2': '[O][O]',
        'oxygen': '[O][O]',
        'benzyl': '[CH2]c1ccccc1',
        'phenyl': '[c]1ccccc1',
    }
    identifier = identifier.strip()
    molecule = Molecule()
    if not identifier:
        logging.error('Invalid empty identifier.')
        return
    elif identifier.startswith('InChI=1'):
        try:
            molecule.from_inchi(identifier)
        except:
            logging.error('Invalid InChI identifier.')
            return
    elif identifier.lower() in known_names:
        molecule.from_smiles(known_names[identifier.lower()])
    else:
        for char in ['u', 'p', 'c', '{']:
            if char not in identifier.lower():
                try:
                    molecule.from_smiles(identifier)
                except (KeyError, AtomTypeError):
                    logging.error('Invalid SMILES identifier.')
                    return
                except (IOError, ValueError):
                    url = "https://cactus.nci.nih.gov/chemical/structure/{0}/smiles".format(
                        urllib.parse.quote(identifier))
                    try:
                        f = urllib.request.urlopen(url, timeout=10)
                    except:
                        logging.error('Invalid identifier for NCI resolver.')
                        return
                    smiles = f.read().decode('utf-8')
                    try:
                        molecule.from_smiles(smiles)
                    except (KeyError, AtomTypeError):
                        logging.error('Invalid identifier.')
                break
        else:
            try:
                molecule.from_adjacency_list(identifier)
            except:
                logging.error('Invalid adjacency list identifier.')
                return
    return molecule
