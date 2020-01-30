#!/usr/bin/python
#-*- coding: utf-8 -*-
""" 
Script to convert from LIS annotation to keras-yolo3 annotation. LIS annotation has the form:

```
id_frame \t label \t (x,y,w,h) \t bbox_id \t path
```

The output is the keras-yolov3 annotation in the format:

```
Path xmin,ymin,xmax,ymax,class_id xmin,ymin,xmax,ymax,class_id
``` 
"""
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import argparse
from PIL import Image
import os
import ast
from os.path import join


def change_annotation(fan, fout, dclasses):
    """
    Change annotation from original LIS annotation as:
        id_frame \t label \t (x,y,w,h) \t bbox_id \t path
    To keras-yolov3 annotation as:
        Path xmin,ymin,xmax,ymax,class_id xmin,ymin,xmax,ymax,class_id
    """ 
    last_index = 0
    positions = ''
    with open(fan) as fin:
        for i, line in enumerate(fin):
            #Frame \t Label \t Points \t Bounding Box ID \t Frame path
            arr = line.strip().split('\t')
            if arr[0].isdigit():
                index = int(arr[0])
                if index != last_index and i != 1:
                    fout.write('%s%s\n' % (path, positions)) 
                    positions = ''
                    last_index = index
                path = arr[4]
                xmin, ymin, w, h = ast.literal_eval(arr[2])
                if xmin < 0: xmin = 0
                if ymin < 0: ymin = 0
                xmax = xmin+w
                ymax = ymin+h
                label = arr[1]
                if not dclasses.has_key(label):
                    dclasses[label] = len(dclasses)
                class_id = dclasses[arr[1]]
                positions += ' %d,%d,%d,%d,%d' % (xmin, ymin, xmax, ymax, class_id)
        fout.write('%s%s\n' % (path, positions))
    return dclasses
                

def main(folder_annotation, output):
    """
    Convert from LIS annotation to keras-yolov3 annotation
    Save annotation in `yolo_annotation.txt` and class ids in `classes.txt`
    """  
    dclasses = {}
    if not output:
        output = folder_annotation
    foutput = join(output, 'yolo_annotation.txt')
    fclasses = join(output, 'classes.txt')

    with open(foutput, 'w') as fout, open(fclasses, 'w') as fclout:
        for root, dirs, files in sorted(os.walk(folder_annotation)):
            for file in files:
                if file == 'Bounding_Boxes_Annotation.txt':
                    fannot = join(root, file)
                    logger.info('Opening file: {}'.format(fannot))
                    dclasses = change_annotation(fannot, fout, dclasses)
        sorted_classes = sorted(dclasses.items(), key=lambda kv: kv[1])
        for k, v in sorted_classes:
            fclout.write('%s\n' % k)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('annotation_folder', metavar='folder_annotation', help='Path to the folder containing annotations')
    argparser.add_argument('-o', '--output', help='Folder to save annotation and class labels', default=None)
    args = argparser.parse_args()

    main(args.annotation_folder, args.output)

