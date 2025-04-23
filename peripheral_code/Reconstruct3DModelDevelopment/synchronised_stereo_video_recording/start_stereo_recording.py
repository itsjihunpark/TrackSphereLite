import subprocess
from datetime import datetime
import os
"""
record_video_both.sh args

width_crop=$1 eg) 1440
height_crop=$2 eg) 1088
width_record=$3 eg) 1440
height_record=$4 eg) 1080
fps=$5 eg) 30
shutter=$6 eg) 1000
frameno_source=$7 eg) 100
frameno_sink=$8 eg) 99
dest_sink=$9 eg) some/path/to/[timestamp]_sink.mp4
dest_source=$10 eg) some/path/to/[timestamp]_source.mp4
dest_source_temp=$11 eg) some/path/to/[timestamp]_source_temp.mp4
dest_sink_ts=$12 eg) some/path/to/[timestamp]_sink/[timestamp]_sink.txt
dest_source_ts=$13 eg) some/path/to/[timestamp]_sink/[timestamp]_source.txt
"""
BASE_PATH = "/home/j-p/Documents/cv_pipe/camera_util_scripts/example/stereo_recording_rpicam_vid"
now = datetime.now()
DATETIME = now.strftime("%Y%m%d_t_%H%M%S")

width_crop = str(1440)
height_crop = str(320)
width_record = str(1440)
height_record = str(320)
fps = str(10)
shutter = str(1000)
frameno_source = str(100)
frameno_sink = str(99)
dest_sink = str(os.path.join(BASE_PATH,f"{DATETIME}_sink.mp4"))
dest_source = str(os.path.join(BASE_PATH,f"{DATETIME}_source.mp4"))
dest_source_temp = str(os.path.join(BASE_PATH,f"{DATETIME}_source_temp.mp4"))
dest_sink_ts = str(os.path.join(BASE_PATH,f"{DATETIME}_sink.txt"))
dest_source_ts = str(os.path.join(BASE_PATH,f"{DATETIME}_source.txt"))

subprocess.call(['sh', './record_video_both.sh', width_crop, height_crop, width_record, height_record, fps, shutter, frameno_source, frameno_sink, dest_sink, dest_source, dest_source_temp, dest_sink_ts, dest_source_ts])


