#!/usr/bin/env python
# coding: utf-8
"""
This script receives a file containing a list of paths to images and performs the prediction
for each image. The output file contains the name of the file, the bounding box coordinates,
the class of the bounding box and its score of confidence.
"""
import warnings
warnings.filterwarnings('ignore')
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

import _init_paths
import os
import sys
import numpy as np
import argparse
import cv2
import torch
from torch.autograd import Variable

from scipy.misc import imread
from model.utils.config import cfg
from model.rpn.bbox_transform import clip_boxes
from model.nms.nms_wrapper import nms
from model.rpn.bbox_transform import bbox_transform_inv
from model.utils.net_utils import vis_detections
from model.utils.blob import im_list_to_blob
#from model.faster_rcnn.vgg16 import vgg16
from model.faster_rcnn.resnet import resnet
from os.path import exists, basename, join, dirname

import progressbar as pbar


def check_files(list_files):
    for path in list_files:
        if not exists(path):
            logger.error('Path for file does not exist: {}'.format(path))
            sys.exit(0)
    return

def load_classes(fclass, dic=False, inverse=True):
    """ Load classes in a numpy array, where the id corresponds to
        the index of the array.
    """
    dclasses = {}
    classes = []
    with open(fclass) as fin:
        for line in fin:
            id, label = line.strip().split()
            if dic:
                if inverse: dclasses[label] = id
                else: dclasses[id] = label
            else:
                classes.append(label)
    if dic: 
        return dclasses
    logger.info('Loaded {} classes.'.format(len(classes)))
    return np.array(classes)


def load_image_paths(finput):
    """ From a text file containing paths to images, return a list with all paths """
    imglist = []
    with open(finput) as fin:
        for line in fin:
            arr = line.strip().split()
            imglist.append(arr[0])
    logger.info('Loaded {} images.'.format(len(imglist)))
    return imglist


def _get_image_blob(im):
    """Converts an image into a network input.
        Arguments:
        im (ndarray): a color image in BGR order
        Returns:
        blob (ndarray): a data blob holding an image pyramid
        im_scale_factors (list): list of image scales (relative to im) used
          in the image pyramid
    """
    im_orig = im.astype(np.float32, copy=True)
    im_orig -= cfg.PIXEL_MEANS

    im_shape = im_orig.shape
    im_size_min = np.min(im_shape[0:2])
    im_size_max = np.max(im_shape[0:2])

    processed_ims = []
    im_scale_factors = []

    for target_size in cfg.TEST.SCALES:
        im_scale = float(target_size) / float(im_size_min)
        # Prevent the biggest axis from being more than MAX_SIZE
        if np.round(im_scale * im_size_max) > cfg.TEST.MAX_SIZE:
          im_scale = float(cfg.TEST.MAX_SIZE) / float(im_size_max)
        im = cv2.resize(im_orig, None, None, fx=im_scale, fy=im_scale,
                interpolation=cv2.INTER_LINEAR)
        im_scale_factors.append(im_scale)
        processed_ims.append(im)
    # Create a blob to hold the input images
    blob = im_list_to_blob(processed_ims)
    return blob, np.array(im_scale_factors)


def write_detections(fout, imname, id_class, dets, threshold=0.5, round_prec=2):
    """ Write detections in a file. """
    for i in range(np.minimum(10, dets.shape[0])):
        bbox = tuple(int(np.round(x)) for x in dets[i, :4])
        xmin, ymin, xmax, ymax = bbox
        score = dets[i, -1]
        if score > threshold:
            fout.write('{};{};{};{};{};{};{}\n'.format(imname, xmin, ymin, xmax, ymax, id_class, round(score, round_prec)))
    return


def main(finput, foutput, fmodel, fclass):
    """ Predict images from `fileinput` using `model` and saves predictions in `output`. """
    if not foutput:
        foutput = join(dirname(finput), 'predictions.csv')
    fout = open(foutput, 'w')
    fout.write('Frame;xmin;ymin;xmax;ymax;id_class;score\n')
    check_files([finput, fmodel, fclass])
    pascal_classes = load_classes(fclass)
    dic_classes = load_classes(fclass, dic=True, inverse=True)

    load_name = fmodel
    # initilize the network here.
    #if args.net == 'vgg16':
    #fasterRCNN = vgg16(pascal_classes, pretrained=False, class_agnostic=args.class_agnostic)
    fasterRCNN = resnet(pascal_classes, 101, pretrained=False, class_agnostic=False)
    fasterRCNN.create_architecture()

    logger.info("Load checkpoint %s" % (load_name))
    checkpoint = torch.load(load_name)
    fasterRCNN.load_state_dict(checkpoint['model'])
    if 'pooling_mode' in checkpoint.keys():
        cfg.POOLING_MODE = checkpoint['pooling_mode']
    logger.info('load model successfully!')

    # initilize the tensor holder here.
    im_data = torch.FloatTensor(1)
    im_info = torch.FloatTensor(1)
    num_boxes = torch.LongTensor(1)
    gt_boxes = torch.FloatTensor(1)

    # ship to cuda
    im_data = im_data.cuda()
    im_info = im_info.cuda()
    num_boxes = num_boxes.cuda()
    gt_boxes = gt_boxes.cuda()

    # make variable
    im_data = Variable(im_data, volatile=True)
    im_info = Variable(im_info, volatile=True)
    num_boxes = Variable(num_boxes, volatile=True)
    gt_boxes = Variable(gt_boxes, volatile=True)

    fasterRCNN.cuda()
    fasterRCNN.eval()

    max_per_image = 100
    thresh = 0.05

    imglist = load_image_paths(finput)
    num_images = len(imglist)
    logger.info('Loaded Photo: {} images.'.format(num_images))

    pb = pbar.ProgressBar(num_images)
    for im_file in imglist:
        im_in = np.array(imread(im_file))
        # rgb -> bgr
        im = im_in[:,:,::-1]

        im_blob, im_scales = _get_image_blob(im)
        im_info_np = np.array([[im_blob.shape[1], im_blob.shape[2], im_scales[0]]], dtype=np.float32)

        im_data_pt = torch.from_numpy(im_blob)
        im_data_pt = im_data_pt.permute(0, 3, 1, 2)
        im_info_pt = torch.from_numpy(im_info_np)

        im_data.data.resize_(im_data_pt.size()).copy_(im_data_pt)
        im_info.data.resize_(im_info_pt.size()).copy_(im_info_pt)
        gt_boxes.data.resize_(1, 1, 5).zero_()
        num_boxes.data.resize_(1).zero_()

        rois, cls_prob, bbox_pred, \
        rpn_loss_cls, rpn_loss_box, \
        RCNN_loss_cls, RCNN_loss_bbox, \
        rois_label = fasterRCNN(im_data, im_info, gt_boxes, num_boxes)

        scores = cls_prob.data
        boxes = rois.data[:, :, 1:5]

        # Apply bounding-box regression deltas
        box_deltas = bbox_pred.data
        # Optionally normalize targets by a precomputed mean and stdev
        box_deltas = box_deltas.view(-1, 4) * torch.FloatTensor(cfg.TRAIN.BBOX_NORMALIZE_STDS).cuda() \
                       + torch.FloatTensor(cfg.TRAIN.BBOX_NORMALIZE_MEANS).cuda()
        box_deltas = box_deltas.view(1, -1, 4 * len(pascal_classes))

        pred_boxes = bbox_transform_inv(boxes, box_deltas, 1)
        pred_boxes = clip_boxes(pred_boxes, im_info.data, 1)
        pred_boxes /= im_scales[0]

        scores = scores.squeeze()
        pred_boxes = pred_boxes.squeeze()
        im2show = np.copy(im)
        coordinates = []
        for j in xrange(1, len(pascal_classes)):
            inds = torch.nonzero(scores[:,j]>thresh).view(-1)
            # if there is det
            if inds.numel() > 0:
                cls_scores = scores[:,j][inds]
                _, order = torch.sort(cls_scores, 0, True)
                cls_boxes = pred_boxes[inds][:, j * 4:(j + 1) * 4]

                cls_dets = torch.cat((cls_boxes, cls_scores.unsqueeze(1)), 1)
                # cls_dets = torch.cat((cls_boxes, cls_scores), 1)
                cls_dets = cls_dets[order]
                keep = nms(cls_dets, cfg.TEST.NMS, force_cpu=not cfg.USE_GPU_NMS)
                cls_dets = cls_dets[keep.view(-1).long()]
                #im2show = vis_detections(im2show, pascal_classes[j], cls_dets.cpu().numpy(), 0.5)
                class_name = pascal_classes[j]
                write_detections(fout, basename(im_file)[:-4], dic_classes[class_name], cls_dets.cpu().numpy(), 0.5)
            
        #result_path = os.path.join('/home/roger/', basename(im_file)[:-4] + "_det.jpg")
        #logger.info('Saved file: {}'.format(result_path))
        #cv2.imwrite(result_path, im2show)
        pb.update()
    fout.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fileinput', metavar='input_file', help='File containing paths to images')
    parser.add_argument('model', metavar='pth_model', help='File .pth containing the trained model.')
    parser.add_argument('-o', '--output', help='Path to a file where the predictions are saved.', default=None)
    parser.add_argument('-c', '--classes', help='Path to a file containing a list of classes.', default='classes.cfg')
    args = parser.parse_args()
    
    main(args.fileinput, args.output, args.model, args.classes)

