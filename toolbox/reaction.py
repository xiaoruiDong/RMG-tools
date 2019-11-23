#!/usr/bin/env python3
"""
The toolbox for reaction related tasks
"""

import logging
import re
from copy import deepcopy

from rmgpy.molecule.molecule import Molecule
from rmgpy.species import Species
from rmgpy.kinetics.arrhenius import Arrhenius, MultiArrhenius, PDepArrhenius

from toolbox.species import add_spc_to_spc_dict

##################################################################

def parse_rxn_label(label, spc_dict, interactive=False, resonance=True):
    """
    Convert reaction label to reactants, products and reversible

    Args:
        label (str): reaction label in RMG style
        spc_dict (OrderedDict): an ordered dictionary has all species information
        interactive (bool): if parse in an interactive way
        resonance (bool): if generate resonance structure for reactants and product
    """
    # Make a copy of species dictionary to avoid overwriting
    spc_dict_backup = deepcopy(spc_dict)
    # Check if reaction arrow contained
    arrow = re.search(r'[<]?[=][>]', label).group()
    if not arrow:
        logging.error('The reaction label %s is not legal' %(label))
        return
    # Parse the reaction label into species labels
    [left, right] = label.split(arrow)
    if left and right:
        reactant_labels = [label.strip() for label in left.split("+")]
        product_labels = [label.strip() for label in right.split("+")]
    else:
        # Check if any side is empty
        logging.error('The reaction label %s is not legal' % (label))
        return
    # Check if species is not parsable by species dictionary
    for label in reactant_labels + product_labels:
        # Modify the label or extend species dictionary if interactive mode
        if label not in spc_dict_backup and interactive:
            add_or_correct = 'wrong'
            logging.info('Species label "%s" is not recoganizable.' %(label))
            while add_or_correct.lower() not in 'add' \
                    and add_or_correct.lower() not in 'correct':
                add_or_correct = input('Add a species (type "add") or correct the label (type "correct"):')
                if add_or_correct.lower() in 'add':
                    # If successful return new label, nonetype otherwise
                    new_label = add_spc_to_spc_dict('', '', spc_dict_backup, interactive=True)
                elif add_or_correct.lower() in 'correct':
                    new_label = input('Enter the correct species label:')
                else:
                    new_label = None
                if new_label in spc_dict_backup and label in reactant_labels:
                    reactant_labels[reactant_labels.index(label)] = new_label
                elif new_label in spc_dict_backup and label in product_labels:
                    product_labels[product_labels.index(label)] = new_label
                else:
                    add_or_correct = 'wrong'
                    logging.error('Invalid addition or correction.')
        elif label not in spc_dict_backup:
            logging.error("label %s is not in the species dict." % (label))
            return
    reactants = [spc_dict_backup[label] for label in reactant_labels]
    products = [spc_dict_backup[label] for label in product_labels]
    spc_dict.update(spc_dict_backup)
    if resonance:
        for reactant in reactants:
            reactant.generate_resonance_structures()
        for product in products:
            product.generate_resonance_structures()
    return reactants, products


def get_arrhenius_from_param(params, settings, arrh_type='Arrhenius'):
    """
    Get Arrhenius object given params and settings
    
    Args:
        params (dict) : A dictionary contains the information about
                        A factor, n, Ea, T0 and multiplier
        settings (dict): A dictionary contains the information about
                         variable units, T and P range, description
        arrh_type (str): The type of Arrhenius object to be added,
                         supporting Arrhenius, MultiArrhenius, and
                         PdepArrehnius
    
    Returns:
        (Arrhenius object): The Arrhenius object generated
    """
    args = {}
    if 'Tmin' in settings and settings['Tmin']:
        args['Tmin'] = (settings['Tmin'], settings['T_unit'])
    if 'Tmax' in settings and settings['Tmax']:
        args['Tmax'] = (settings['Tmax'], settings['T_unit'])
    if 'Pmin' in settings and settings['Pmin']:
        args['Pmin'] = (settings['Pmin'], settings['P_unit'])
    if 'Pmax' in settings and settings['Pmax']:
        args['Pmax'] = (settings['Pmax'], settings['P_unit'])
    if 'comment' in settings and settings['comment']:
        args['comment'] = settings['comment']

    if arrh_type == 'Arrhenius':
        args['A'] = (params['A'], settings['A_unit'])
        args['n'] = params['n']
        args['Ea'] = (params['Ea'], settings['E_unit'])
        if 'T0' in params and params['T0']:
            args['T0'] = (params['T0'], settings['T_unit'])
        if 'uncertainty' in params and params['uncertainty']:
            args['uncertainty'] = params['uncertainty']
        return Arrhenius(**args)
    elif arrh_type == 'MultiArrhenius':
        args['arrhenius'] = params['arrhenius']
        return MultiArrhenius(**args)
    elif arrh_type == 'PdepArrhenius':
        args['arrhenius'] = params['arrhenius']
        args['pressures'] = (params['pressures'], settings['P_unit'])
        if 'highPlimit' and params['highPlimit']:
            args['highPlimit'] = params['highPlimit']
        return PDepArrhenius(**args)


def get_kinetic_data(k_data, settings):
    """
    Get Arrhenius object given params and settings
    
    Args:
        k_data (dict) : A dictionary contains the information about
                        A factor, n, Ea, T0 and multiplier
        settings (dict): A dictionary contains the information about
                         variable units, T and P range, description
    
    Returns:
        data (RMG Kinetics): RMG kinetics data can be used to generate
                             rate coefficients or added to RMG Entry
    """
    for k_type, params in k_data.items():
        if not params['active']:
            continue
        if k_type == 'Arrhenius':
            data = get_arrhenius_from_param(params, settings)
        elif k_type == 'MultiArrhenius':
            if len(params['A']) == len(params['n']) and \
               len(params['A']) == len(params['Ea']):
                mult_params = {'arrhenius': []}
                for index in range(len(params['A'])):
                    arrh_params = {
                       'A': params['A'][index],
                       'n': params['n'][index],
                       'Ea': params['Ea'][index],
                       }
                    if 'T0' in params:
                        arrh_params['T0'] = params['T0']
                    mult_params['arrhenius'].append(
                        get_arrhenius_from_param(arrh_params, settings))
                print(mult_params)
                data = get_arrhenius_from_param(mult_params,
                                settings, arrh_type=k_type)
            else:
                logging.error('A, n and Ea does not have same length.')
                return
        elif k_type == 'PdepArrhenius':
            if len(params['A']) == len(params['n']) and \
               len(params['A']) == len(params['Ea']) and \
               len(params['A']) == len(params['P']):
                pdep_params = {'arrhenius': [],
                                    'pressures': params['P'],
                                    'highPlimit': None}
                for index in range(len(params['A'])):
                    arrh_params = {
                        'A': params['A'][index],
                        'n': params['n'][index],
                        'Ea': params['Ea'][index],
                    }
                    if 'T0' in params:
                        arrh_params['T0'] = params['T0']
                    if isinstance(params['P'], str) and \
                       params['P'] == 'inf':
                        pdep_params['highPlimit'] = get_arrhenius_from_param(
                                                        arrh_params, settings)
                        pdep_params['pressures'].remove('inf')
                    else:
                        pdep_params['arrhenius'].append(
                            get_arrhenius_from_param(arrh_params, settings))
                data = get_arrhenius_from_param(pdep_params,
                                                settings, arrh_type=k_type)
            else:
                logging.error('Not support the kinetic type.')
                return
        if 'multiplier' in params.keys() and params['multiplier']:
            data.change_rate(params['multiplier'])
        break
    else:
        logging.error('No active kinetic parameter data.')
        return
    return data
