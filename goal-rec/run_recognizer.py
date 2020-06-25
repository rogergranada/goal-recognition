#!/usr/bin/env python
# coding: utf-8
"""

"""
import os
import argparse
from os.path import join, dirname, basename, isfile, isdir
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import subprocess
from subprocess import Popen
import math
import pandas as pd

import filehandler as fh


def check_group(relations, groups):
    """ Check if there are groups in elements of the relations.
        If so, create a relation for the type of group.

    Parameters:
    -----------
    relations: array
        list containing triplets of relations
    groups: dict
        dictionary containing the name of the group as key and its components as value
    
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


def show_goals(candidate_goals):
    for cgoal in candidate_goals:
        score = float(cgoal.split(': ')[1])
        for k in KEYS:
            if k in cgoal:
                logger.info(k, type(score))


def add_goals(i, goal_scores, candidate_goals, goals):
    for candidate in candidate_goals:
        score = float(candidate.split(': ')[1])
        for goal in goals:
            if goal in candidate:
                if math.isnan(score):
                    score = -1
                if goal in goal_scores:
                    goal_scores[goal].append(score)
                else:
                    goal_scores[goal] = [score]


class GoalRecognizer(object):
    def __init__(self):
        self.recognizer = Popen(['java', '-jar', 'gc_stop.jar'], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)

    def check_goals(self):
        self.recognizer.stdin.write(b"r\r\n")
        self.recognizer.stdin.write(b"x\r\n")
        self.recognizer.stdin.flush()
        line = self.recognizer.stdout.readline()
        sp = []
        while (line != b"x\n"):
            sp.append(str(line).replace('\'', '').replace('\\n',('')))
            line = self.recognizer.stdout.readline()
            if line == b'EOF\n':
                self.recognizer.stdin.write(b"x\r\n")
                self.recognizer.stdin.flush()
                break;
        return sp


class FileObservations(object):
    def __init__(self, fname):
        self.fname = fname
        self._clear_file()
        self.fout = open(fname, 'a')

    def _clear_file(self):
        open(self.fname, 'w').close()

    def write_observation(self, observation):
        self.fout.write('{}\n'.format(observation))
        self.fout.flush()
        os.fsync(self.fout.fileno())

    def __str__(self):
        return 'File for observations: {}'.format(self.fname) 

    def __del__(self):
        self.fout.close()


def save_scores(fname, goal_scores):
    logger.info('Saving scores into file: {}'.format(fname))
    df = pd.DataFrame.from_dict(goal_scores, orient="index")
    df = df.transpose()
    df.to_csv(fname)


def run_file(fileinput, folder_output, initfile='pddl.ini'):
    """ Perform goal recognition in a single file.

    Parameters:
    -----------
    fileinput: string
        path to the DecompressedFile containing relations
    """
    finit = fh.PDDLInit(initfile)
    groups = finit.groups
    goals = finit.goals
    fname = fh.filename(fileinput, extension=False)
    fnameout = 'scores_{}.csv'.format(fname)
    foutput = join(folder_output, fnameout)
    goal_scores = {}
    rec = GoalRecognizer()
    fobs = FileObservations('demo/obs.dat')

    fd = fh.DecompressedFile(fileinput)
    last_relations = []
    candidate_goals = []
    for idfr, relations in fd.iterate_frames():
        relations = check_group(relations, groups)
        if relations != last_relations:
            logger.info('Processing frame: {}'.format(idfr))
            last_relations = relations
            str_rels = convert_relations_string(relations)
            fobs.write_observation(str_rels)
            candidate_goals = rec.check_goals()
        else:
            candidate_goals = candidate_goals
        add_goals(idfr, goal_scores, candidate_goals, goals)
    save_scores(foutput, goal_scores)


def run_multiple(folder_input, output):
    """ 

    Parameters:
    -----------
    folder_input: string
        path to the folder containing files with relations
    output: string
        path to the file where the goals are saved.
    """
    if not output:
        output = dirname(folder_input)
 
    relfiles = fh.FolderHandler(folder_input)
    for file_input in relfiles:
        logger.info('Reading file: {}'.format(file_input))
        fname = fh.filename(file_input, extension=False)
        run_file(file_input, output)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='input_folder', help='Folder containing Decompressed relations.')
    parser.add_argument('-o', '--output', help='Folder to save the score files', default=None)
    args = parser.parse_args()

    if isfile(args.input):
        run_file(args.input, args.output)
    elif isdir(args.input):
        run_multiple(args.input, args.output)
    
