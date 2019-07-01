#!/usr/bin/python
#-*- coding: utf-8 -*-
""" 
Convert the keras-yolov3 annotation for images in a certain size (e.g., 256x256) 
to images with a different size (e.g., 416x416). Input file has the format:

```
Path xmin,ymin,xmax,ymax,class_id xmin,ymin,xmax,ymax,class_id
``` 
"""
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import argparse
from os.path import join, dirname, splitext, basename
import progressbar as pb


def count_lines(inputfile):
    """ Count the number of lines of the inputfile """
    with open(inputfile) as fin:
        for n, _ in enumerate(fin, start=1): pass
    return n


def main(inputfile, size_in, size_out):
    """
    Convert annotation from size_in to size_out images.
    """  
    fname, _ = splitext(basename(inputfile))
    foutname = fname+'_'+str(size_out)+'.txt'
    foutput = join(dirname(inputfile), foutname)

    pbar = pb.ProgressBar(count_lines(inputfile))
    with open(foutput, 'w') as fout, open(inputfile) as fin:
        for i, line in enumerate(fin):
            #image.jpg xmin,ymin,xmax,ymax,id xmin,ymin,xmax,ymax,id
            arr = line.strip().split()
            pos_str = arr[0]
            for position in arr[1:]:
                xmin, ymin, xmax, ymax, id = position.split(',')
                xmin_out = int((float(xmin)/size_in) * size_out)
                ymin_out = int((float(ymin)/size_in) * size_out)
                xmax_out = int((float(xmax)/size_in) * size_out)
                ymax_out = int((float(ymax)/size_in) * size_out)
                pos_str += ' %d,%d,%d,%d,%s' % (xmin_out, ymin_out, xmax_out, ymax_out, id)
            fout.write('%s\n' % pos_str)
            pbar.update()
    logger.info('Converted %d files' % i)
    logger.info('Saved output file as: %s' % foutput)
                

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('inputfile', metavar='annotated_file', help='Path to the file containing annotations')
    argparser.add_argument('-i', '--input_size', help='Size of the image in original annotation', default=256, type=int)
    argparser.add_argument('-o', '--output_size', help='Size of the image in output annotation', default=416, type=int)
    args = argparser.parse_args()

    main(args.inputfile, args.input_size, args.output_size)

