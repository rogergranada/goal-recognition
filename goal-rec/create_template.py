#!/usr/bin/env python
# coding: utf-8
"""
This script reads a folder containing files with relations and generates the template with
all objects and possible relations. A recipe must have in common the filename as:

1-boiledegg.txt
2-boiledegg.txt
...
5-boiledegg.txt

The goal state is created using the relations in the last frame of the recipe from a 
decompressed file. When the same object appears in two different places in the last 
frame for the same recipe, the relation is discarded and not included in the goal state.
"""
import sys
import os
import argparse
from os.path import join, dirname, splitext, basename, isfile, isdir
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

import filehandler as fh


def convert_relations_string(objects, relations, groups):
    """ Convert an array of relations into goal states. 

    Parameters:
    -----------
    relations: array
        list containing tuples of relations

    Example:
    --------
    >>> convert_relations_string([(A, on, B), (C typeC)])
        "(A),(B),(typeC),(on A1 B1),(typeC C)"
    """
    content = '(:init\n'
    for obj in objects:
        if obj not in groups:
            content += '  ({} {}1)\n'.format(obj, obj)
    for arr in sorted(relations):
        if len(arr) == 2:
            s, o = arr
            content += '  ({} {}1)\n'.format(s, o)
        elif len(arr) == 3:
            s, r, o = arr
            content += '  ({} {}1 {}1)\n'.format(r, s, o)
    content += ')\n'
    return content


def convert_objects_string(objects):
    """ Convert objects into elements to (:objects 

    Parameters:
    -----------
    objects: array
        list containing objects
    """
    content = '(:objects\n'
    for obj in objects:
        content += '  {}1\n'.format(obj)
    content += ')\n'
    return content


def save_template(problem, domain, objects, relations, groups, fname):
    """ Convert relations into string of goals and save it in a file.
    
    Parameters:
    -----------
    dobj: dict
        dictionary with objects as key
    drel: dict
        dictionary with relations as key
    fname: string
        path to the output file
    """
    content = '(define (problem {})\n'.format(problem)
    content += '(:domain {})\n'.format(domain)
    content += convert_objects_string(objects)
    content += convert_relations_string(objects, relations, groups)
    content += '(:goal (and\n'
    content += '  <HYPOTHESIS>\n'
    content += '))\n)'

    with open(fname, 'w') as fout:
        fout.write(content)


def check_group(groups, relations):
    """ Check if there are groups in elements of the relations.
        If so, create a relation for the type of group.

    Parameters:
    -----------
    relations: array
        list containing triplets of relations
    
    Example:
    --------
    >>> check_group([('ham_egg', 'on', 'A'), ('B', 'holding', 'shell_egg')])
        [('egg', 'on', 'A'), ('B', 'holding', egg'), 
         ('hamm_egg', 'egg), ('shell_egg', 'egg')]
    """ 
    addegg = []
    for i in range(len(relations)):
        s, r, o = relations[i]
        if s in groups['egg']:
            addegg.append((s, 'egg'))
            s = 'egg'
        if o in groups['egg']:
            addegg.append((o, 'egg'))
            o = 'egg'
        relations[i] = (s, r, o)
    return relations+addegg
            


def generate_template(pddlinit, output, problem='pbkitchen', domain='kscgr'):
    """ Generate a file containing the template for a set of files
        containing relations between objects. 

    Parameters:
    -----------
    folder_input: string
        path to the folder containing files with relations
    output: string
        path to the file where the template is saved.
    """
    if not output:
        output = join(dirname(pddlinit), 'template.pddl')
        
    finit = fh.PDDLInit(initfile=pddlinit)
    groups = finit.groups
    objects = finit.objects
    relations = finit.init_states
    relations = check_group(groups, relations)
    logger.info('Loaded {} relations.'.format(len(relations)))
    logger.info('Saving goal states in: {}'.format(output))
    save_template(problem, domain, objects, relations, groups, output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--initfile', metavar='pddl_ini', help='pddl.ini file with configuration', default='pddl.ini')
    parser.add_argument('-o', '--output', help='Plain text file', default=None)
    args = parser.parse_args()

    generate_template(args.initfile, args.output)
    
