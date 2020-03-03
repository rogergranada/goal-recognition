#!/usr/bin/python
#-*- coding: utf-8 -*-
""" 
Functions that can be used for many scripts.
"""
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import os
from os.path import realpath, join, splitext, dirname


def count_lines(inputfile):
    """ Count the number of lines of the inputfile """
    with open(inputfile) as fin:
        for n, _ in enumerate(fin, start=1): pass
    return n


def list_files(inputfolder, type='.jpg'):
    """ Returns a list of .jpg files from the input folder """
    files = os.listdir(inputfolder)
    names = []
    for fname in files:
        name, ext = splitext(fname)
        if type == '.jpg' and ext == '.jpg':
            names.append(int(name))
        elif type == '.avi' and ext == '.avi':
            names.append(join(dirname(inputfolder), fname))
    return names


def create_pathfile(inputfolder, outputfile=None, images=True):
    if not outputfile:
        outputfile = join(inputfolder, 'paths.txt')

    if images:
        list_names = list_files(inputfolder, type='.jpg')
    else:
        list_names = list_files(inputfolder, type='.avi')

    with open(outputfile, 'w') as fout:
        for name in sorted(list_names):
            if images:
                name = join(inputfolder, str(name)+'.jpg')
            fout.write('%s\n' % name)
    logger.info('Saved paths in file: %s' % outputfile)
    return outputfile
