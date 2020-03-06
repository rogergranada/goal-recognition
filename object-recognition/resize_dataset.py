#!/usr/bin/python
#-*- coding: utf-8 -*-
""" 
Script to resize KSCGR dataset from its original size (640,480,3) to YOLOv3 size (416,416,3).

Input file has the form "<path_to_image> <true_label>" as:

```
path/data1/boild-egg/0.jpg 0
```

"""
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import argparse
import os
import cv2
from os.path import join, realpath, dirname, isdir

import progressbar as pb
from utils import count_lines


def resize_image(img, size):
    """
    Resize a image to `size`

    Parameters:
    -----------
    img : numpy.ndarray
        image after read by cv2.imread()
    size : int
        new size of the image
    """
    width = int(img.shape[1])
    height = int(img.shape[0])
    new_width = 0
    crop = 0

    if width < height:
        new_width = size
        new_height = int((size * height) / width)
        crop = new_height - size
        img = cv2.resize(img, (new_width, new_height), 0, 0, cv2.INTER_CUBIC)
        half_crop = int(crop / 2)
        img = img[crop / 2:size + half_crop, :]
    else:
        new_height = size
        new_width = int((size * width) / height)
        crop = new_width - size
        img = cv2.resize(img, (new_width, new_height), 0, 0, cv2.INTER_CUBIC)
        half_crop = int(crop / 2)
        img = img[:, half_crop:size + half_crop]
    return img


def create_path(inputfile, outputdir):
    """ Change the path of the inputfile to the outputdir folder """
    pathdata = '/'.join(inputfile.split('/')[-3:])
    newpath = join(outputdir, pathdata)
    dirout = dirname(newpath)
    if not isdir(dirout):
        os.makedirs(dirout)
    return newpath
    

def main(inputfile, output, size):
    """
    Resize images from `fileinput` to `size` by `size`, saving the output
    images in `output` folder.
    """
    if not output:
        output = join(dirname(inputfile), str(size))
        if not isdir(output):
            os.mkdir(output)

    logger.info('Resizing images from: %s' % inputfile)
    inputfile = realpath(inputfile)
    #/usr/share/datasets/KSCGR_Original/data1/boild-egg/0.jpg 0
    nb_lines = count_lines(inputfile)
    pbar = pb.ProgressBar(nb_lines)
    with open(inputfile) as fin:
        for line in fin:
            path, tl = line.strip().split()
            newpath = create_path(path, output)
            img = cv2.imread(path)
            img = resize_image(img, size)
            cv2.imwrite(newpath, img)
            pbar.update()
    logger.info('Total of images resized: %d' % nb_lines)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('inputfile', metavar='input_file', help='File containing paths of images and true labels (paths.txt)')
    argparser.add_argument('-o', '--output', help='Folder to save images with the new size', default=None)
    argparser.add_argument('-s', '--size', help='Size of the output images', default=416, type=int)
    args = argparser.parse_args()

    main(args.inputfile, args.output, args.size)

