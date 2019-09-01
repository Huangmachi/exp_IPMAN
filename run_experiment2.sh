#!/bin/bash
# Copyright (C) 2019 Huang MaChi at China Mobile Communication
# Corporation, Zhanjiang, Guangdong, China.

den=$1
cpu=$2
tnum=$3
duration=$4
out_dir=$5
k_paths=$6

# Exit on any failure.
set -e

# Check for uninitialized variables.
set -o nounset

ctrlc() {
	killall python
	killall -9 ryu-manager
	mn -c
	exit
}

trap ctrlc INT

# Run experiments.
# Create iperf peers.
sudo python ./create_peers.py --den $den
sleep 1

# SDIPMAN
dir=$out_dir/$tnum/SDIPMAN
mkdir -p $dir
mn -c
sudo python ./SDIPMAN/topo_ipman.py --den $den --cpu $cpu --duration $duration --dir $dir --k_paths $k_paths

# IPMAN
dir=$out_dir/$tnum/IPMAN
mkdir -p $dir
mn -c
sudo python ./IPMAN/ipman.py --den $den --cpu $cpu --duration $duration --dir $dir --k_paths $k_paths


