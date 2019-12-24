#!/usr/bin/python
#-*- coding: utf-8 -*-
""" 
Create `gt.pkl` containing a Python dictionary with the following keys: 

'sub_bboxes' : tuple with the bounding boxes of the subjects in the image
    d['sub_bboxes'].shape == (1, nb_images)
    d['sub_bboxes'][0][N].shape == (nb_relations, BBOX), where BBOX = [xmin, xmax, ymin, ymax]
'obj_bboxes' : tuple with the bounding boxes of the objects in the image
    d['obj_bboxes'].shape == (1, nb_images)
    d['obj_bboxes'][0][N].shape == (nb_relations, BBOX), where BBOX = [xmin, xmax, ymin, ymax]
'tuple_label': tuple with the ids of subject, relation and object for each element in the image
    d['tuple_label'].shape == (1, nb_images)
    d['tuple_label'][0][N].shape == (nb_relations, REL), where REL = [isubj, irel, iobj]
"""
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import argparse
from os.path import join, dirname, splitext, basename
from collections import defaultdict

import filehandler as fh
import numpy as np
import cPickle
import operator

import progressbar as pbar 

def add_element(element, vec):
    if not len(element):
        element = np.array([vec])
    else:
        element = np.append(element, [vec], axis=0)
    return element


def create_gt_pickle(fileobj, filerel, output=None, class_file='classes.cfg', rels_file='relations.cfg'):
    """
    Create a `gt.pkl` file containing the relationship between subjects and objects. 

    TODO: Implement relations for two objects of the same class in the same image
    """  
    if not output:
        output = join(dirname(fileobj), 'gt.pkl')

    dgt = {'sub_bboxes': [], 'obj_bboxes': [], 'tuple_label': []}
   
    # Load classes for objects from dict {0: 'rel0', 1: 'rel1'}
    # DO NOT LOAD `__background__`. Thus, id_person=0
    do = fh.ConfigFile(class_file, background=False).load_classes(cnames=True)
    logger.info('Loaded dictionary with {} objects.'.format(len(do)))
    dr = fh.ConfigFile(rels_file).load_classes(cnames=True)
    logger.info('Loaded dictionary with {} relations.'.format(len(dr)))

    dic_rels = defaultdict(list) # relations for each image
    logger.info('Loading information from file: {}'.format(filerel))
    filerls = fh.DecompressedFile(filerel)
    pb = pbar.ProgressBar(filerls.nb_lines())
    with filerls as frels:
        for fr, o1, r, o2, path in frels:
            idsub = do[o1]
            idrel = dr[r]
            idobj = do[o2]
            pathimg = join(path, str(fr)+'.jpg')
            dic_rels[pathimg].append((idsub, idrel, idobj))
            pb.update()
    print
    # Load objects
    logger.info('Loading information from file: {}'.format(fileobj))
    flis = fh.LisFile(fileobj)
    nb_frames = filerls.nb_frames()
    pb = pbar.ProgressBar(nb_frames)
    logger.info('Processing {} frames.'.format(nb_frames))
    with flis as fin:
        for pathimg, arr in flis.iterate_frames():
            sub_boxes, obj_boxes, vrels = [], [], []
            for idsub, idrel, idobj in dic_rels[pathimg]:
                relation = np.array([idsub, idrel, idobj])
                for i in range(len(arr)):
                    obj, x, y, w, h = arr[i]
                    iobj = do[obj]
                    if iobj == idsub:
                        bbox_sub = np.array([x, y, x+w, y+h])
                    if iobj == idobj:
                        bbox_obj = np.array([x, y, x+w, y+h])
                sub_boxes = add_element(sub_boxes, bbox_sub)
                obj_boxes = add_element(obj_boxes, bbox_obj)
                vrels = add_element(vrels, relation)
                   
            dgt['sub_bboxes'].append(sub_boxes)
            dgt['obj_bboxes'].append(obj_boxes)
            dgt['tuple_label'].append(vrels)
            pb.update()
    
    dgt['sub_bboxes'] = np.array(dgt['sub_bboxes'])
    dgt['obj_bboxes'] = np.array(dgt['obj_bboxes'])
    dgt['tuple_label'] = np.array(dgt['tuple_label'])
    logger.info('Saving pickle file...')
    fout = open(output, 'wb')
    cPickle.dump(dgt, fout)
    fout.close()
    logger.info('Saved content in file: {}'.format(output))
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('objfile', metavar='file_objects', help='Path to the file containing relations between objects.')
    parser.add_argument('relfile', metavar='file_relations', help='Path to the file containing relations between objects.')
    parser.add_argument('-o', '--output', help='Path to the file to save the conditional probabilities.')
    parser.add_argument('-c', '--cfg_objects', help='File containing ids and their classes', default='classes.cfg')
    parser.add_argument('-r', '--cfg_relations', help='File containing ids and their relations', default='relations.cfg')
    args = parser.parse_args()

    create_gt_pickle(args.objfile, args.relfile, args.output, args.cfg_objects, args.cfg_relations)

