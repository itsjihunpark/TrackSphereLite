

width_crop=$1
height_crop=$2
width_record=$3
height_record=$4
fps=$5
shutter=$6
frameno_source=$7
frameno_sink=$8
dest_sink=$9
dest_source="${10}"
dest_sink_ts="${11}"
dest_source_ts="${12}"

/bin/bash ./bvts_config/configure_cameras.sh "$width_crop" "$height_crop"

sleep 1

echo $width_crop
echo $height_crop
echo $width_record
echo $height_record
echo $fps
echo $shutter
echo $frameno_source
echo $frameno_sink
echo $dest_sink
echo $dest_source
echo $dest_sink_ts
echo $dest_source_ts

rpicam-vid --no-raw --camera 1 --width $width_record --height $height_record --denoise cdn_off --framerate $fps --frames $frameno_source --shutter $shutter -o $dest_source -n &
sleep 0.5
rpicam-vid --no-raw --camera 0 --width $width_record --height $height_record --denoise cdn_off --framerate $fps --frames $frameno_sink --shutter $shutter -o $dest_sink -n


ffprobe $dest_source -hide_banner -select_streams v -show_entries frame | grep pts_time > $dest_source_ts
ffprobe $dest_sink -hide_banner -select_streams v -show_entries frame | grep pts_time > $dest_sink_ts

/bin/bash ./bvts_config/configure_cameras.sh "1456" "1088"