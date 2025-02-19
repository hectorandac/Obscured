#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import argparse
import os
import sys
import os.path as osp

import torch

ROOT = os.getcwd()
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from yolov6.utils.events import LOGGER
from yolov6.core.inferer import Inferer


def get_args_parser(add_help=True):
    parser = argparse.ArgumentParser(description='YOLOv6 PyTorch Inference.', add_help=add_help)
    parser.add_argument('--weights', type=str, default='weights/yolov6s.pt', help='model path(s) for inference.')
    parser.add_argument('--source', type=str, default='data/images', help='the source path, e.g. image-file/dir.')
    parser.add_argument('--webcam', action='store_true', help='whether to use webcam.')
    parser.add_argument('--webcam-addr', type=str, default='0', help='the web camera address, local camera or rtsp address.')
    parser.add_argument('--yaml', type=str, default='data/coco.yaml', help='data yaml file.')
    parser.add_argument('--img-size', nargs='+', type=int, default=[640, 640], help='the image-size(h,w) in inference size.')
    parser.add_argument('--conf-thres', type=float, default=0.4, help='confidence threshold for inference.')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold for inference.')
    parser.add_argument('--max-det', type=int, default=1000, help='maximal inferences per image.')
    parser.add_argument('--device', default='0', help='device to run our model i.e. 0 or 0,1,2,3 or cpu.')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt.')
    parser.add_argument('--not-save-img', action='store_true', help='do not save visuallized inference results.')
    parser.add_argument('--save-dir', type=str, help='directory to save predictions in. See --save-txt.')
    parser.add_argument('--view-img', action='store_true', help='show inference results')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by classes, e.g. --classes 0, or --classes 0 2 3.')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS.')
    parser.add_argument('--project', default='runs/inference', help='save inference results to project/name.')
    parser.add_argument('--name', default='exp', help='save inference results to project/name.')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels.')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences.')
    parser.add_argument('--half', action='store_true', help='whether to use FP16 half-precision inference.')
    parser.add_argument('--analyze', action='store_true', help='Extract the region importance based on the detections made on a sample of the scene.')
    parser.add_argument('--masks', type=str, help='Path to the masks.pt file. The masks are used to enhance inference performance by selectively ignoring sections of the image per detection head, based on the provided mask regions, allowing the model to focus only on areas of interest.')
    parser.add_argument('--inference_with_mask', action='store_true', help='Flag to determine whether to perform inference with the provided masks, allowing the model to focus only on the areas of interest and potentially enhancing performance.')
    parser.add_argument('--enable-gater-net', action='store_true', help='Enables the gater-net at the neck level to recognize unused filters.')
    parser.add_argument('--enable-fixed-gates', action='store_true', help='Enables the gater-net at the neck level to recognize unused filters.')
    parser.add_argument('--fixed-gates', type=str, help='Enables the gater-net at the neck level to recognize unused filters.')


    args = parser.parse_args()
    LOGGER.info(args)
    return args


@torch.no_grad()
def run(weights=osp.join(ROOT, 'yolov6s.pt'),
        source=osp.join(ROOT, 'data/images'),
        webcam=False,
        webcam_addr=0,
        yaml=None,
        img_size=640,
        conf_thres=0.4,
        iou_thres=0.45,
        max_det=1000,
        device='',
        save_txt=False,
        not_save_img=False,
        save_dir=None,
        view_img=True,
        classes=None,
        agnostic_nms=False,
        project=osp.join(ROOT, 'runs/inference'),
        name='exp',
        hide_labels=False,
        hide_conf=False,
        half=False,
        analyze=False,
        inference_with_mask=False,
        masks=None,
        enable_gater_net=False,
        fixed_gates=None,
        enable_fixed_gates=False
        ):
    """ Inference process, supporting inference on one image file or directory which containing images.
    Args:
        weights: The path of model.pt, e.g. yolov6s.pt
        source: Source path, supporting image files or dirs containing images.
        yaml: Data yaml file, .
        img_size: Inference image-size, e.g. 640
        conf_thres: Confidence threshold in inference, e.g. 0.25
        iou_thres: NMS IOU threshold in inference, e.g. 0.45
        max_det: Maximal detections per image, e.g. 1000
        device: Cuda device, e.e. 0, or 0,1,2,3 or cpu
        save_txt: Save results to *.txt
        not_save_img: Do not save visualized inference results
        classes: Filter by class: --class 0, or --class 0 2 3
        agnostic_nms: Class-agnostic NMS
        project: Save results to project/name
        name: Save results to project/name, e.g. 'exp'
        line_thickness: Bounding box thickness (pixels), e.g. 3
        hide_labels: Hide labels, e.g. False
        hide_conf: Hide confidences
        half: Use FP16 half-precision inference, e.g. False
    """
    # create save dir
    # Function to get the next available directory name with an incremental number
    def get_next_dir_name(base_dir, name):
        counter = 1
        new_dir = osp.join(base_dir, f"{name}{counter}")
        while osp.exists(new_dir):
            counter += 1
            new_dir = osp.join(base_dir, f"{name}{counter}")
        return new_dir

    if save_dir is None:
        save_dir = osp.join(project, name)
        save_txt_path = osp.join(save_dir, 'labels')
    else:
        save_txt_path = save_dir

    # Check if directory exists and create a new one with an incremental number if necessary
    if (not not_save_img or save_txt):
        if not osp.exists(save_dir):
            os.makedirs(save_dir)
        else:
            LOGGER.warning('Save directory already existed. Creating a new directory with an incremental number.')
            save_dir = get_next_dir_name(project, name)  # Update save_dir with new directory name
            os.makedirs(save_dir)
            save_txt_path = osp.join(save_dir, 'labels')

    if save_txt:
        if not osp.exists(save_txt_path):
            os.makedirs(save_txt_path)

    # Inference
    inferer = Inferer(source, webcam, webcam_addr, weights, device, yaml, img_size, half, enable_gater_net, fixed_gates, enable_fixed_gates)
    inferer.infer(
        conf_thres, iou_thres, classes, agnostic_nms, max_det, save_dir, save_txt, not not_save_img,
        hide_labels, hide_conf, view_img, analyze, enable_gater_net)

    if save_txt or not not_save_img:
        LOGGER.info(f"Results saved to {save_dir}")


def main(args):
    run(**vars(args))


if __name__ == "__main__":
    args = get_args_parser()
    main(args)
