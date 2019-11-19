#!/usr/bin/env python3
"""
The ARC Tool box
"""
import os
import re
import datetime
import numpy as np
import matplotlib.pyplot as plt
import shutil
import glob
import logging
from copy import deepcopy

from arc import settings
from arc.main import ARC
from arc.job.ssh import SSHClient, write_file
from arc.common import read_yaml_file, save_yaml_file
from arc.parser import parse_xyz_from_file
from arc.job.job import Job
from arc.settings import servers, check_status_command, submit_command, submit_filename, delete_command

from arkane.statmech import determine_qm_software
from arc.species.converter import get_xyz_string, molecules_from_xyz, rdkit_conf_from_mol, set_rdkit_dihedrals, get_xyz_matrix

from rmgpy.data.thermo import ThermoLibrary
##################################################################

def delete_arkane_output(project_directory, species_label_list):
    """
    Delete the arkane output files according to the species list provided, besides
    it will also delete other file like RMG library
    """
    output_directory = os.path.join(project_directory, "output")
    for item in os.listdir(output_directory):
        if "Species" not in item:
            path_to_remove = os.path.join(output_directory, item)
            logging.info("Removing {0}...".format(item))
            remove_folder_or_file(path_to_remove)
    for species_label in species_label_list:
        delete_species_arkane_output(output_directory, species_label)

    logging.info("All done.")

def delete_species_arkane_output(output_directory, species_label):
    """
    Delete the arkane output files according to the species list provided
    """
    species_output_folder = os.path.join(output_directory,"Species",species_label)
    remove_flag = False
    for item in os.listdir(species_output_folder):
        if "arkane" in item:
            path_to_remove = os.path.join(species_output_folder, item)
            remove_folder_or_file(path_to_remove)
            remove_flag = True
        if "yml" in item:
            os.remove(os.path.join(species_output_folder, item))
            remove_flag = True
    if remove_flag:
        logging.info("Arkane output files of species {0} are all removed".format(species_label))
    else:
        logging.info("Nothing is deleted for species {0}".format(species_label))

def remove_folder_or_file(path_to_remove):
    """
    Remove folder or file given the path to the file/folder
    """
    if os.path.isdir(path_to_remove):
        shutil.rmtree(path_to_remove)
    elif os.path.isfile(path_to_remove):
        os.remove(path_to_remove)

def remove_unnecessary_calc(project_directory, JOB):
    """
    Remove calculation results not used in arkane jobs to save disk space.
    """
    not_remove_dict = scan_critical_calc(JOB)
    calc_species_path = os.path.join(project_directory,"calcs","Species")

    for species_label in os.listdir(calc_species_path):
        logging.info("Clean up the calculation of {0}...".format(species_label))
        species_path = os.path.join(calc_species_path, species_label)
        if species_label in not_remove_dict.keys():
            for job_name in os.listdir(species_path):
                if job_name == "conformers":
                    continue
                for job_dirs in not_remove_dict[species_label].values():
                    if job_name in job_dirs:
                        remove = False
                        break
                    else:
                        remove = True
                if remove:
                    logging.info("Removed job {0}".format(job_name))
                    remove_folder_or_file(os.path.join(species_path,job_name))

        elif os.path.isdir(species_path):
            shutil.move(species_path, os.path.join(calc_species_path,"[-]"+species_label))
            logging.info("Label species {0} as unconverged".format(species_label))

def scan_critical_calc(JOB):
    """
    Find all output file paths in the restart file
    """
    not_remove_dict = {}
    for species_label, output_dict in JOB.output.items():
        if "ALL converged" in output_dict["status"]:
            not_remove_dict[species_label] = {}
            for key, item in output_dict.items():
                if key != "status":
                    not_remove_dict[species_label][key]=item

    for species in JOB.as_dict()["species"]:
        if species["label"] in not_remove_dict.keys():
            rotors_dict = species["rotors_dict"]
            for rotor in rotors_dict.values():
                not_remove_dict[species["label"]][str(rotor["pivots"])] = rotor["scan_path"]
    return not_remove_dict

def change_critical_calc_path(input_dict, project_directory, new_project_directory):
    """
    Change the paths in restart file.
    """
    for species_label, output_dict in input_dict["output"].items():
        for key in output_dict:
            if key != "status":
                input_dict["output"][species_label][key] = re.sub(project_directory,\
                    new_project_directory, input_dict["output"][species_label][key])

    for species in input_dict["species"]:
        rotors_dict = species["rotors_dict"]
        for rotor in rotors_dict.values():
            rotor["scan_path"] = re.sub(project_directory, new_project_directory, rotor["scan_path"])
    save_yaml_file(path=os.path.join(project_directory, "restart.yml"), content=input_dict)
    logging.info("Changed the paths in the restart file.")

def migrate_project(project_directory, new_project_directory, input_dict):
    """
    Move the project from project_directory to new_project_directory
    """
    change_critical_calc_path(input_dict,project_directory, new_project_directory)
    shutil.move(project_directory, os.path.dirname(os.path.dirname(new_project_directory)))

def get_all_jobs_in_directory(project_directory):
    """
    Find all the scan jobs in the calcs folder
    """
    species_dict = {}
    # All jobs for species stored in the /project_directory/calcs/Species/
    species_root_path = os.path.join(project_directory, "calcs", "Species")
    # find species in the /Species/ folder
    for species in get_sub_dirs(species_root_path):
        # Except conformer jobs, other jobs are listed under /Species/species/
        species_path = os.path.join(species_root_path, species)
        species_dict[species] = [job for job in get_sub_dirs(species_path)
                if job!="conformers"]
        # Conformer jobs are listed under /Species/species/conformers/conform_id/
        conformers_path = os.path.join(species_path, "conformers")
        if os.path.isdir(conformers_path):
            for conformer_id in get_sub_dirs(conformers_path):
                conformer_job_path = os.path.join(conformers_path, conformer_id)
                for conformer_job in get_sub_dirs(conformer_job_path):
                    species_dict[species].append(conformer_job)
    return species_dict

def get_sub_dirs(path):
    sub_dir_list = [sub_dir for sub_dir in os.listdir(path)
                    if os.path.isdir(os.path.join(path, sub_dir))]
    return sub_dir_list


def find_species_by_job_name(project_directory, job_name):
    """
    Find the species according to the job name
    """
    species_dict = get_all_jobs_in_directory(project_directory)
    # Find the corresponding species
    for species_label, jobs in species_dict.iteritems():
        if job_name in jobs:
            return species_label
    else:
        raise Exception("Specified job not found")

def find_job_path(JOB, project_directory, job_name, servers, server):
    """
    Find the job local and server job path
    """
    species_label = find_species_by_job_name(project_directory, job_name)
    local_path = os.path.join(project_directory,"calcs","Species",species_label,job_name)
    species_name_for_remote_path = species_label.replace('(', '_').replace(')', '_')
    remote_path = os.path.join('/home',servers[server]["un"],'runs', 'ARC_Projects', JOB.project,
                                        species_name_for_remote_path, job_name)
    return local_path, remote_path

def find_scan_info_from_input_file(local_path, input_filename):
    """
    parse the scan job input file
    """
    scan_trsh = "\n"
    pivot = None
    local_input_path = os.path.join(local_path, input_filename)
    with open(local_input_path, "r") as f:
        for line in f.readlines():
            if re.search("D[\s\d]+[\s\d]+[\s\d]+[\s\d]+[\s]+S", line.strip()):
                pivot = [int(line.split(" ")[2]), int(line.split(" ")[3])]
                scan = [int(line.split(" ")[1]),int(line.split(" ")[2]), int(line.split(" ")[3]), int(line.split(" ")[4])]
                scan_res = float(line.split(" ")[-1])
            if re.search("D[\s\d]+[\s\d]+[\s\d]+[\s\d]+[\s]+F", line.strip()):
                scan_trsh += re.search("D[\s\d]+[\s\d]+[\s\d]+[\s\d]+[\s]+F", line.strip()).group() + '\n'
    if scan_trsh == "\n":
            scan_trsh = ''
    if pivot:
        return (pivot, scan, scan_res, scan_trsh)
    else:
        return (None, None, None, None)

def get_job_memory(JOB, servers, server, software):
    memory = JOB.memory
    cpus = servers[server].get('cpus', 8)  # set to 8 by default
    if software == 'molpro':
        memory = memory * 128 / cpus
    if software == 'terachem':
        memory = memory * 128 / cpus
    elif software == 'gaussian':
        memory = memory * 1000
    elif software == 'orca':
        memory = memory * 1000 / cpus
    elif software == 'qchem':
        memory = memory  # dummy
    elif software == 'gromacs':
        memory = memory  # dummy
    return memory

def generate_running_scan_job_dict(input_dict):
    """
    Generate the running scan job dictionary
    """
    running_jobs = {}
    if not "running_jobs" in input_dict.keys():
        return running_jobs
    for species, jobs in input_dict["running_jobs"].iteritems():
        running_jobs[species] = {}
        for job in jobs:
            if job["job_type"] == "scan":
                running_jobs[species][job["job_name"]]=job["pivots"]
        if not running_jobs[species]:
            running_jobs.pop(species, None)
    return running_jobs

def read_job_num(output_path):
    """
    Extract job num from the job_path
    """
    job_name = output_path.split("/")[-2]
    job_num = int(job_name.split('_')[-1][1:])
    return job_num

def compare_pivot(pivot1, pivot2):
    """
    Compare pivot1 and pivot2 regardless of the sequence
    """
    if pivot1 == pivot2 or pivot1 == [pivot2[-1], pivot2[0]]:
        return True
    else:
        return False

def obtain_scan_job_status(input_dict):
    rotor_status = {}
    running_scan_jobs = generate_running_scan_job_dict(input_dict)

    for species in input_dict["species"]:
        rotor_status[species["label"]] = {}
        for rotor in species["rotors_dict"].itervalues():
            # 1. Check whether running:
            if species["label"] in running_scan_jobs.keys():
                for job_name, pivot in running_scan_jobs[species["label"]].iteritems():
                    if compare_pivot(pivot, rotor["pivots"]):
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Running", job_name)
                        break
            if str(rotor["pivots"]) in rotor_status[species["label"]].keys():
                continue

            # 2. Check if it is a job converged before any corrections
            job_num = 0
            if rotor["scan_path"]:
                job_num = read_job_num(rotor["scan_path"])
                if "opt" in input_dict["output"][species["label"]].keys():
                    job_opt_num = read_job_num(input_dict["output"][species["label"]]["opt"])
                elif "composite" in input_dict["output"][species["label"]].keys():
                    job_opt_num = read_job_num(input_dict["output"][species["label"]]["composite"])
                else:
                    rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: unknown reason 1", "scan_a"+str(job_num))
                    continue
                # Scan can not be earlier than opt
                if job_num < job_opt_num:
                    pivot_from_scan = rotor["scan"][1:3]
                    if compare_pivot(pivot_from_scan, rotor["pivots"]):
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: Converged before comformer correction", "scan_a"+str(job_num))
                        continue
                    else:
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: scan changed to {0} given pivot {1}".format(rotor["scan"],rotor["pivots"]), "scan_a"+str(job_num))
                        continue
                # Check symmetry
                if "symmetry" in rotor.keys():
                    if rotor["success"] and rotor["symmetry"]:
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Successfully converged", "scan_a"+str(job_num))
                        continue
                    else:
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: unknown reason 1", "scan_a"+str(job_num))
                        continue
                elif rotor["success"]:
                    rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: End job without troubleshooting", "scan_a"+str(job_num))
                    continue

                # job converged, but the range is too large
                if "larger" in rotor["invalidation_reason"]:
                    rotor_status[species["label"]][str(rotor["pivots"])] = ("Converged but invalid", "scan_a"+str(job_num))
                    continue

                # job converged, but the consecutiive points are inconsistent by XX kJ/mol
                if "consecutive" in rotor["invalidation_reason"]:
                    rotor_status[species["label"]][str(rotor["pivots"])] = ("Converged but invalid", "scan_a"+str(job_num))
                    continue

                # job not converged
                if "crash" in rotor["invalidation_reason"]:
                    # job not converged and no output in local
                    if not os.path.isfile(rotor["scan_path"]):
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: Scan never start or unexpected termination", "scan_a"+str(job_num))
                        continue
                    with open(rotor["scan_path"]) as f:
                        lines = f.readlines()
                    if not lines:
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: Empty output caused by unexpected termination", "scan_a"+str(job_num))
                        continue
                    for line in lines[-1:-20:-1]:
                        if 'Normal termination of Gaussian' in line:
                            rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: unknown reason 2", "scan_a"+str(job_num))
                            break
                    else:
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: ESS not converged", "scan_a"+str(job_num))
                        continue
                    continue
                else:
                    rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: unknown reason 3", "scan_a"+str(job_num))
                    continue
            else:
                if "running_jobs" in input_dict.keys():
                    if species["label"] in input_dict["running_jobs"].keys():
                        for job in input_dict["running_jobs"][species["label"]]:
                            if job["job_type"] == "composite" or job["job_type"] == "opt":
                                rotor_status[species["label"]][str(rotor["pivots"])] = ("Running preliminary job", "N/A")
                                break
                elif "opt" not in input_dict["output"][species["label"]].keys() or "composite" not in input_dict["output"][species["label"]].keys():
                        rotor_status[species["label"]][str(rotor["pivots"])] = ("Running preliminary job or conformer jobs fail", "N/A")
                else:
                    rotor_status[species["label"]][str(rotor["pivots"])] = ("Error: unknown reason 4", "scan_a"+str(job_num))
    return rotor_status

def rotate_molecule_to_lowest_conformer(arkane_log, local_path, input_filename, multiplicity = 1, charge = 0,):
    """
    Given the input file, rotate the molecule to lowest conformer
    args:
        arkane_log: the gaussian file read by Arkane
        local_path (str): local path to the job
        input_filename (str): the name of the input file
        multiplicity (int)
        charge (int)
    return:
        xyz (str): the xyz string used in arc geometry or gaussian geometry input
    """
    # Find the degree to rotate
    v_list, angle = arkane_log.loadScanEnergies()
    v_list = np.array(v_list, np.float64)
    point = np.argmin(v_list)
    res = 360.0 / (len(v_list) - 1)
    deg_increment = point * res

    # Find the xyz geometry
    coords, numbers,_ = arkane_log.loadGeometry()
    coords = coords.tolist()
    xyz = get_xyz_string(coords=coords, numbers=numbers)

    # Find the pivot and scan
    pivot, scan, _, _ =  find_scan_info_from_input_file(local_path, input_filename)

    # Change the structure
    mol = molecules_from_xyz(xyz, multiplicity=multiplicity, charge=charge)[1]
    conf, rd_mol, indx_map = rdkit_conf_from_mol(mol, coords)
    rd_scan = [indx_map[i-1] for i in scan]
    new_xyz = set_rdkit_dihedrals(conf, rd_mol, indx_map, rd_scan, deg_increment=deg_increment)
    return get_xyz_string(coords=new_xyz, numbers=numbers)
