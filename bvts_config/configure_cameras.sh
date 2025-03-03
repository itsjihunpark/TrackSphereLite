#!/bin/bash

width=$1
height=$2
x="x"

for i in {0..5}; do media-ctl -d /dev/media$i --set-v4l2 "'imx296 10-001a':0 [fmt:SBGGR10_1X10/$width${x}$height crop:($(( (1456 - $width) / 2 )),$(( (1088 - $height) / 2 )))/$width${x}$height]" -v ; [ $? -eq 0 ] && break; done
for i in {0..5}; do media-ctl -d /dev/media$i --set-v4l2 "'imx296 11-001a':0 [fmt:SBGGR10_1X10/$width${x}$height crop:($(( (1456 - $width) / 2 )),$(( (1088 - $height) / 2 )))/$width${x}$height]" -v ; [ $? -eq 0 ] && break; done


echo "'imx296 10-001a':0 [fmt:SBGGR10_1X10/$width${x}$height crop:($(( (1456 - $width) / 2 )),$(( (1088 - $height) / 2 )))/$width${x}$height]"
echo "'imx296 11-001a':0 [fmt:SBGGR10_1X10/$width${x}$height crop:($(( (1456 - $width) / 2 )),$(( (1088 - $height) / 2 )))/$width${x}$height]"

libcamera-hello --list-camera 
