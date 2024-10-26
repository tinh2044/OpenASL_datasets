import os
import json
import math
import cv2
import sys
import glob
import subprocess
import shutil
import tempfile
import argparse
import numpy as np
import json
from tqdm import tqdm
import pandas as pd


def crop_resize(imgs, bbox, target_size):
    x0, y0, x1, y1 = bbox[0], bbox[1], bbox[2], bbox[3]
    if x1 - x0 < y1 - y0:
        exp = (y1 - y0 - (x1 - x0)) / 2
        x0, x1 = x0 - exp, x1 + exp
    else:
        exp = (x1 - x0 - (y1 - y0)) / 2
        y0, y1 = y0 - exp, y1 + exp
    x0, x1, y0, y1 = int(x0), int(x1), int(y0), int(y1)
    left_expand = -x0 if x0 < 0 else 0
    up_expand = -y0 if y0 < 0 else 0
    right_expand = x1 - imgs[0].shape[1] + 1 if x1 > imgs[0].shape[1] - 1 else 0
    down_expand = y1 - imgs[0].shape[0] + 1 if y1 > imgs[0].shape[0] - 1 else 0
    rois = []
    for img in imgs:
        expand_img = cv2.copyMakeBorder(img, up_expand, down_expand, left_expand, right_expand, cv2.BORDER_CONSTANT,
                                        (0, 0, 0))
        roi = expand_img[y0 + up_expand: y1 + up_expand, x0 + left_expand: x1 + left_expand]
        roi = cv2.resize(roi, (target_size, target_size))
        rois.append(roi)
    return rois


def write_video_ffmpeg(rois, target_path, ffmpeg):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    decimals = 10
    fps = 25
    tmp_dir = tempfile.mkdtemp()
    for i_roi, roi in enumerate(rois):
        cv2.imwrite(os.path.join(tmp_dir, str(i_roi).zfill(decimals) + '.png'), roi)
    list_fn = os.path.join(tmp_dir, "list")
    with open(list_fn, 'w') as fo:
        fo.write("file " + "'" + tmp_dir + '/%0' + str(decimals) + 'd.png' + "'\n")
    ## ffmpeg
    if os.path.isfile(target_path):
        os.remove(target_path)

    target_path = target_path.replace("-", "_").replace(":", "-")
    print(target_path)
    cmd = [ffmpeg, "-f", "concat", "-safe", "0", "-i", list_fn, "-q:v", "1", "-r", str(fps), '-y', '-crf', '20',
           '-pix_fmt', 'yuv420p', target_path]
    subprocess.run(" ".join(cmd), shell=True)
    # rm tmp dir
    shutil.rmtree(tmp_dir)
    print(f"Saved ROIs to {target_path}")
    return


def crop_video(input_video_dir, output_video_dir, tsv_fn, bbox_fn, rank, nshard, target_size=224, ffmpeg=None):
    os.makedirs(output_video_dir, exist_ok=True)
    df = pd.read_csv(tsv_fn, sep='\t')
    vid2bbox = json.load(open(bbox_fn))
    items = []
    for vid, yid, start, end in zip(df['vid'], df['yid'], df['start'], df['end']):
        if not os.path.exists(f"{input_video_dir}/{yid}.mp4"): continue
        if vid not in vid2bbox:
            continue
        bbox = vid2bbox[vid]
        items.append([vid, yid, start, end, bbox])
    num_per_shard = (len(items) + nshard - 1) // nshard
    items = items[num_per_shard * rank: num_per_shard * (rank + 1)]
    print(f"{len(items)} videos")
    i = 0
    for vid, yid, start_time, end_time, bbox in tqdm(items):
        input_video_whole, output_video = os.path.join(input_video_dir, yid + '.mp4'), os.path.join(output_video_dir,
                                                                                                    vid + '.mp4')
        output_video = output_video.replace("-", "_").replace(":", "-")
        print(output_video)
        if os.path.isfile(output_video):
            continue
        tmp_dir = tempfile.mkdtemp()
        input_video_clip = os.path.join(tmp_dir, 'tmp.mp4')
        cmd = [ffmpeg, '-ss', start_time, '-to', end_time, '-i', input_video_whole, '-c:v', 'libx264', '-crf', '20',
               output_video]
        if not os.path.exists(input_video_whole):
            print(input_video_whole)
            continue
        print(' '.join(cmd))
        subprocess.run(" ".join(cmd), shell=True)
        # cap = cv2.VideoCapture(input_video_clip)
        # frames_origin = []
        # print(f"Reading video clip: {input_video_clip}")
        # while True:
        #     ret, frame = cap.read()
        #     if not ret:
        #         break
        #     frames_origin.append(frame)
        # cap.release()
        # # shutil.rmtree(tmp_dir)

        # x0, y0, x1, y1 = bbox
        # W, H = frames_origin[0].shape[1], frames_origin[0].shape[0]
        # bbox = [int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)]
        # print(bbox, frames_origin[0].shape, target_size)
        # rois = crop_resize(frames_origin, bbox, target_size)
        # write_video_ffmpeg(rois, output_video, ffmpeg=ffmpeg)
        i += 1

        if i == 100:
            return
    return


def main():
    tsv = "../data/openasl-v1.0.csv"
    bbox = "../data/bbox-v1.0.json"
    src_dir = "../splitting_video/"
    dest_dir = "../crop_video/"
    ffmpeg = 'ffmpeg'
    target_size = 512

    crop_video(dest_dir, src_dir, tsv, bbox, 0, 1, target_size=target_size, ffmpeg=ffmpeg)


if __name__ == '__main__':
    main()
