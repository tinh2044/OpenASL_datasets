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

logs_dict = {
    "src_not_exists": [],
    "not_found_bbox": [],
    "split_videos": [],
    "(w_h0)":

}


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


def xyxy2xywh(bbox, width=None, height=None):
    x0, y0, x1, y1 = bbox
    if width is not None and height is not None:
        x0, y0, x1, y1 = x0 * width, y0 * height, x1 * width, y1 * height
    return [x0, y0, x1 - x0, y1 - y0]


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

    # target_path = target_path.replace("-", "_").replace(":", "-")
    print(target_path)
    cmd = [ffmpeg, "-f", "concat", "-safe", "0", "-i", list_fn, "-q:v", "1", "-r", str(fps), '-y', '-crf', '20',
           '-pix_fmt', 'yuv420p', target_path]
    subprocess.run(" ".join(cmd), shell=True)
    # rm tmp dir
    shutil.rmtree(tmp_dir)
    print(f"Saved ROIs to {target_path}")
    return


def get_clip(input_video_dir, output_video_dir, tsv_fn, bbox_fn, rank, nshard, target_size=224, ffmpeg=None):
    os.makedirs(output_video_dir, exist_ok=True)
    df = pd.read_csv(tsv_fn, sep=',')
    vid2bbox = json.load(open(bbox_fn))
    items = []
    for idx, row in df.iterrows():
        row = row.to_dict()
        yid, vid = row['yid'], row['vid']
        if not os.path.exists(f"{input_video_dir}/{yid}.mp4"):
            logs_dict['src_not_exists'].append(f"{input_video_dir}/{yid}.mp4")
            continue
        if vid not in vid2bbox:
            logs_dict['not_found_bbox'].append(vid)
            continue
        output_video = f"{output_video_dir}/{vid}.mp4"
        if os.path.exists(output_video):
            logs_dict['split_videos'].append(output_video)
            continue
        bbox = vid2bbox[vid]
        items.append({**row, 'bbox': bbox})

    print(f"{len(items)} videos")

    for item in tqdm(items):
        total, used, free = shutil.disk_usage(output_video_dir)
        free_gb = free / (1024 ** 3)
        if free_gb < 10:
            print("10GG remaining disk space")
            return

        yid, vid, start_time, end_time = item['yid'], item['vid'], item['start'], item['end']
        width, height = item['video_width'], item['video_height']

        bbox = item['bbox']
        input_video = f"{input_video_dir}/{yid}.mp4"
        output_video = f"{output_video_dir}/{vid}.mp4"
        if width == 0 or height == 0:
            logs_dict['(w_h0)'].append(output_video)
            continue
        # output_video = output_video.replace("-", "_").replace(":", "-")
        if os.path.exists(output_video):
            logs_dict['split_videos'].append(output_video)
            continue

        x, y, w, h = xyxy2xywh(bbox, width, height)
        # tmp_dir = tempfile.mkdtemp()
        if w > width:
            w = width
        if h > height:
            h = height

        if w < 0:
            w = 0
        if h < 0:
            h = 0

        # input_video_clip = os.path.join(tmp_dir, 'tmp.mp4')

        cmd = [
            'ffmpeg',
            '-ss', start_time,
            '-to', end_time,
            '-i', input_video,
            '-vf', f"crop={w}:{h}:{x}:{y},scale={target_size}:{target_size}",
            # '-c:v', 'libx264',
            # '-crf', '20',
            '-c:a', 'copy',
            output_video
        ]

        if not os.path.exists(input_video):
            print(f"{input_video} not exists!!!")
            continue
        subprocess.run(" ".join(cmd), shell=True)

        os.system("clear")
    return


def main():
    tsv = "../data/openasl-v3.0.csv"
    bbox = "../data/bbox-v3.0.json"
    raw = "../raw_video/"
    output = "../splitting_video/"
    ffmpeg = 'ffmpeg'
    target_size = 512
    l = []
    get_clip(raw, output, tsv, bbox, 0, 1, target_size=target_size, ffmpeg=ffmpeg)


#     for p in os.listdir(output):
#         l.append(p)
    # with open("../data/splited_video.json", "w") as f:
    #     json.dump(l, f)
if __name__ == '__main__':
    main()
    with open("../data/logs.json", "w") as f:
        json.dump(logs_dict, f)
