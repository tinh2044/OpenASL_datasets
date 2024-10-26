import os
import subprocess


def check_video_errors(video_path):
    # FFmpeg command to check the video for errors
    command = [
        'ffmpeg',
        '-v', 'error',  # Show only errors
        '-i', video_path,  # Input video path
        '-f', 'null', '-'  # Output to null (do not create an output file)
    ]

    # Run the FFmpeg command and capture the output
    process = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    # Decode and return the error messages
    if process.returncode != 0:
        errors = process.stderr.decode('utf-8')
        if errors:
            print(f"Errors found in {video_path}: {errors}")
        else:
            print(f"Unknown error occurred in {video_path}.")


def check_videos_in_directory(directory):
    # Get a list of all files in the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if the file is a video by looking at the extension
            if file.endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')):
                video_path = os.path.join(root, file)
                print(f"Checking video: {video_path}")
                check_video_errors(video_path)


# Example usage
directory_path = '../raw_video'
check_videos_in_directory(directory_path)