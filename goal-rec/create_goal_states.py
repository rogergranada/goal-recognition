#!/usr/bin/env python
# coding: utf-8
"""
This script reads a folder containing files with relations and generates the goal states
for each recipe. A recipe must have in common the filename as:

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


GROUPS = {'egg': ['shell_egg',
                  'boiled_egg', 
                  'hard-boiled_egg', 
                  'broken_egg', 
                  'mixed_egg', 
                  'baked_egg', 
                  'ham_egg', 
                  'kinshi_egg', 
                  'omelette',
                  'scrambled_egg' 
          ]
}


def convert_relations_string(relations):
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
    content = ''
    dobj = {}
    for arr in relations:
        if len(arr) == 2:
            s, o = arr
            content += '({} {}1),'.format(s, o)
        elif len(arr) == 3:
            s, r, o = arr
            dobj[s] = ''
            content += '({} {}1 {}1),'.format(r, s, o)
        dobj[o] = ''
        
    objects = ''
    for obj in dobj:
        objects += '({}1),'.format(obj)
    return objects+content[:-1]


def save_goal(relations, fname):
    """ Convert relations into string of goals and save it in a file.
    
    Parameters:
    -----------
    relations: dict|array
        dictionary or list (for a single file) with relations
    fname: string
        path to the output file
    """
    content = ''
    if type(relations) == dict:
        for recipe in sorted(relations):
            content += convert_relations_string(relations[recipe])+'\n'
    else:
        content = convert_relations_string(relations)
    
    with open(fname, 'w') as fout:
        fout.write(content)


def check_group(relations):
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
        if s in GROUPS['egg']:
            addegg.append((s, 'egg'))
            s = 'egg'
        if o in GROUPS['egg']:
            addegg.append((o, 'egg'))
            o = 'egg'
        relations[i] = (s, r, o)
    return relations+addegg
            

def goal_state_from_file(fileinput, output=None):
    """ Extract the goal state for a single file. 
        In case of having `output`, the goal state is saved into a file.

    Parameters:
    -----------
    fileinput: string
        path to the DecompressedFile containing relations
    output: string (optional)
        path to the output file
    """
    fd = fh.DecompressedFile(fileinput)
    rels = fd.relations_at_frame(fd.nb_frames()-1)
    rels = check_group(rels)
    if output:
        save_goal(rels)
    return rels
    

def add_relations(dic, key, values):
    """ Add relations to the dictionary. When a relation contains a subject
        with multiple objects or relations, this relations is discarded.

    Parameters:
    -----------
    dic: dict
        Dictionary containing fname in the key and list of relations as value
    key: string
        name of the file to keep goals separated by recipe
    values: array
        list of relations to be added to the dictionary

    Example:
    --------
    >>> d = {'f1':[('A','on','B'),('C','in','D')]}
    >>> add_relations(d, 'f1', [('A','in','B'),('E','in','F')])
    >>> print(d)
        {'f1':[('C','in','D'),('E','in','F')]}
    """
    for rel in values:
        remove = []
        if key in dic:
            if rel not in dic[key]:
                for i, arr in enumerate(dic[key]):
                    if rel[0] == arr[0] and (rel[1] != arr[1] or rel[2] != arr[2]):
                        remove.append(i)
                if remove:
                    for i in remove:
                        del dic[key][i]
                else:
                    dic[key].append(rel)
        else:
            rel = list(set(rel))
            dic[key] = [rel]


def generate_goal_states(folder_input, output):
    """ Generate a file containing the goal states for a set of files
        containing relations between objects. Each recipe has its own
        set of goals. Recipes are grouped according to the name of the
        file, where the defaults uses `<nb_file>-<repipe>.txt` format.

    Parameters:
    -----------
    folder_input: string
        path to the folder containing files with relations
    output: string
        path to the file where the goals are saved.
    """
    if not output:
        output = join(folder_input, 'goal_states.dat')
 
    drecipes = {}
    relfiles = fh.FolderHandler(folder_input)
    for file_input in relfiles:
        logger.info('Reading file: {}'.format(file_input))
        fname = fh.filename(file_input, extension=False)[2:]
        relations = goal_state_from_file(file_input)
        add_relations(drecipes, fname, relations)

    logger.info('Saving goal states in: {}'.format(output))
    save_goal(drecipes, output)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='input_folder', help='Plain text file')
    parser.add_argument('-o', '--output', help='Plain text file', default=None)
    args = parser.parse_args()

    if isfile(args.input):
        goal_state_from_file(args.input, args.output)
    elif isdir(args.input):
        generate_goal_states(args.input, args.output)
    
