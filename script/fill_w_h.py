import cv2 as cv
import os
import pandas as pd
from tqdm import tqdm

dict_info = {}
video_dir = "../raw_video"
for p in tqdm(os.listdir(video_dir)):
    if not p.endswith((".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv")):
        continue
    # print(p)
    vid_path = f"{video_dir}/{p}"
    cap = cv.VideoCapture(vid_path)
    ret, frame = cap.read()
    height = frame.shape[0]
    width = frame.shape[1]
    cap.release()
    dict_info[p[:-4]] = [width, height]

df = pd.read_csv("../data/openasl-v3.0.csv")
list_width = []
list_height = []
for i, row in tqdm(df.iterrows(), total=len(df)):

    yid = row['yid']
    if row['video_width'] != 0:
        list_width.append(row['video_width'])
    elif yid in dict_info:
        list_width.append(dict_info[yid][1])
    else:
        list_width.append(0)

    if row['video_height'] != 0:
        list_height.append(row['video_height'])
    elif yid in dict_info:
        list_height.append(dict_info[yid][0])
    else:
        list_height.append(0)

df['video_width'] = list_width
df['video_height'] = list_height
df.to_csv("../data/openasl-v3.0.csv", index=False)