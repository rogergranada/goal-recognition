#/usr/bin/python
import warnings
warnings.filterwarnings('ignore')
import sys
sys.path.insert(0, '..')
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import cv2
import os
import argparse
from os.path import join, basename, dirname, splitext, realpath, isdir

from object_recognition import progressbar as pb
from object_recognition.utils import count_lines, create_pathfile
from object_recognition.images import resize_image


def avi2jpg(inputfile, outputfolder, size=416, border=False):
    """ Extract images from video and save as jpg files """
    print('Loading video: {}'.format(basename(inputfile)))
    video = cv2.VideoCapture(inputfile)
    video_length = int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    success, image = video.read()
    i = 0
    success = True
    pbar = pb.ProgressBar(video_length)
    while success:
        resize_image(image, join(outputfolder, str(i)+'.jpg'), size=size, border=border)
        success, image = video.read()
        i += 1
        pbar.update()
    return i
    

def main(inputfile, outputfolder, size, border):
    if isdir(inputfile):
        inputfile = create_pathfile(inputfile, images=False)

    if not outputfolder:
        outputfolder = dirname(inputfile)

    with open(inputfile) as fin:
        for i, line in enumerate(fin):
            arr = line.strip().split()
            path = arr[0]
            fname, _ = splitext(basename(path))
            outpath = join(outputfolder, fname)
            if not isdir(outpath):        
                os.mkdir(outpath)
            avi2jpg(path, outpath, size=size, border=border)
    print('Converted {} files.'.format(i+1))


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('inputfile', metavar='input_file', help='File containing paths to images')
    argparser.add_argument('-o', '--output', help='Path to the output folder', default=None)
    argparser.add_argument('-s', '--size', help='Size of the squared images', type=int, default=416)
    argparser.add_argument('-b', '--border', help='Add border to make the image squared', action='store_true')
    args = argparser.parse_args()
    main(args.inputfile, args.output, args.size, args.border)
