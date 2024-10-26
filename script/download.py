import os, sys, subprocess, json
from collections import OrderedDict
from tqdm import tqdm
import argparse
import pandas as pd
import shutil


def download_video(vids, target_dir):
    total, used, free = shutil.disk_usage("./")
    free_gb = free / (1024**3)
    if free_gb < 10:
        print("10GG remaining disk space")
        return 
    for url in tqdm(vids):
        if os.path.exists(f"{target_dir}/{url}.mp4'.mp4") or os.path.exists(f"{target_dir}/{url}.mp4"):
            print("File : %s has exists" % url)
        else:
            cmd = ["yt-dlp", url, "-f", "bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
                   "--merge-output-format", "mp4", "--no-check-certificate", "--restrict-filenames", "-o",
                   target_dir + "/%(id)s.%(ext)s" + "'", ]
            subprocess.run(" ".join(cmd), shell=True)
            os.system("cls")
    return


csv_path = "../data\openasl-v1.0.csv"
dest = "../raw_video"
df = pd.read_csv(csv_path, sep='\t')

with open("../data/downloaded_list.json", "r") as f:
    download_file = json.load(f)
yids = sorted(list(set(df['yid'])))
yids = [x for x in yids if x not in download_file]
print(f"Download {len(yids)} raw videos into {dest}")
os.makedirs(dest, exist_ok=True)

download_video(yids, dest)

missing, n_complete = [], 0
for yid in yids:
    dest_fn = f"{dest}/{yid}.mp4"
    if os.path.isfile(dest_fn):
        n_complete += 1
        os.rename(
            dest_fn,
            dest_fn[:-5],
        )
    else:
        missing.append(yid)
print(f"{n_complete}/{len(yids)} videos downloaded successfully.")
if len(missing) > 0:
    fn = f"{dest}/missing.txt"
    with open(fn, "w") as fo:
        fo.write("\n".join(missing) + "\n")
    print(f"List of undownloaded videos saved in {fn}.")

