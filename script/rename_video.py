import os


video_dir = "./raw_video"

for fn in os.listdir(video_dir):
    if fn.endswith("..mp4"):
        os.rename(os.path.join(video_dir, fn), 
        os.path.join(video_dir, fn.replace("..mp4", ".mp4")))