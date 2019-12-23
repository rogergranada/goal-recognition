#!/usr/bin/python
#-*- coding: utf-8 -*-
""" 
Create `proposal.pkl` containing bounding boxes and their probability given the output of the network.
The output file is represented as a dictionary containing the following keys:

'confs' : the confidence scores for bounding boxes
    dic['confs'].shape == (nb_images,)
    dic['confs'][0].shape == (nb_bboxes, 1), where 1 is the prediction score of the bounding box
'boxes' : the coordinates for each bounding box
    dic['boxes'].shape == (nb_images,)
    dic['boxes'][0].shape == (nb_bboxes, 4), where 4 is [xmin, ymin, xmax, ymax] 
'cls' : class of each bounding box
    dic['cls'].shape == (nb_images,)
    dic['cls'].shape == (nb_bboxes, 1), where 1 is the class id
"""
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import argparse
import numpy as np
import cPickle
from os.path import join, dirname, splitext, basename

import progressbar as pbar
import filehandler as fh

def add_element(element, vec, type=np.uint32):
    if not len(element):
        element = np.array([vec], dtype=type)
    else:
        element = np.append(element, [vec], axis=0)
    return element

def prediction_to_proposals(inputfile, output=None, class_file='classes.cfg', rels_file='relations.cfg'):
    """
    Create a `proposal.pkl` file containing bounding boxes and probabilities from predictions. 
    """
    dpkl = {'confs': [], 'boxes': [], 'cls': []}
    if not output:
        output = join(dirname(inputfile), 'proposal.pkl')

    with fh.PredictionFile(inputfile) as fpred:
        pb = pbar.ProgressBar(fpred.nb_frames())
        for idfr, arr in fpred.iterate_frames():
            bbox, scores, classes = [], [], []
            for id_class, xmin, ymin, xmax, ymax, score in arr:
                bbox = add_element(bbox, [xmin, ymin, xmax, ymax])
                scores = add_element(scores, score, type=np.float32)
                classes = add_element(classes, id_class)
            dpkl['confs'].append(scores)
            dpkl['boxes'].append(bbox)
            dpkl['cls'].append(classes)
            pb.update()
    dpkl['confs'] = np.array(dpkl['confs'])
    dpkl['boxes'] = np.array(dpkl['boxes'])
    dpkl['cls'] = np.array(dpkl['cls'])
    
    logger.info('Saving pickle file...')
    fout = open(output, 'wb')
    cPickle.dump(dpkl, fout)
    fout.close()
    logger.info('Saved content in file: {}'.format(output))
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile', metavar='relations_file', help='Path to the file containing relations between objects.')
    parser.add_argument('-o', '--output', help='Path to the file to save the conditional probabilities.')
    parser.add_argument('-c', '--class_file', help='File containing ids and their classes', default='classes.cfg')
    parser.add_argument('-r', '--relation_file', help='File containing ids and their relations', default='relations.cfg')
    args = parser.parse_args()

    prediction_to_proposals(args.inputfile, args.output)

