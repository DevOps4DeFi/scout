#!/bin/bash
## a userdata script to bring an amazon linux 2 instance up and running as a local graph node with badger subgraph
#
#
## Setup Volume
DEVICE=${ebs_device_name}
FS_TYPE=$(file -s $DEVICE | awk '{print $2}')
MOUNT_POINT=${mount_point}
# If no FS, then this output contains "data"
if [ "$FS_TYPE" = "data" ]
then
    echo "Creating file system on $DEVICE"
    mkfs -t xfs $DEVICE
fi
mkdir $MOUNT_POINT
echo "$DEVICE  $MOUNT_POINT  xfs  defaults,nofail  0  2" >> /etc/fstab
mount $MOUNT_POINT

## setup ECS
# The cluster this agent should check into.
echo 'ECS_CLUSTER=${cluster_name}' >> /etc/ecs/ecs.config

## Install docker compose
curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

## Setup mountpoints
mkdir $MOUNT_POINT/prometheus-data
mkdir $MOUNT_POINT/grafana-data
chmod -R 777 $MOUNT_POINT ## required for containers to write