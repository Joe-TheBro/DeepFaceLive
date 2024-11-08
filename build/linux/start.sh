#!/bin/bash

NV_LIB=$(locate nvidia.ko |grep $(uname -r) |grep dkms | head -1)
NV_VER=$(modinfo $NV_LIB | grep ^version |awk '{print $2}'|awk -F '.' '{print $1}')

docker build . -t deepfacelive --build-arg NV_VER=$NV_VER
docker run -d --ipc host --gpus all  -v ../../data/ -p 1234:1234 --device=/dev/video0:/dev/video0 --rm deepfacelive
