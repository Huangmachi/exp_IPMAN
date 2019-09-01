#!/bin/bash
# Copyright (C) 2019 Huang MaChi at China Mobile Communication
# Corporation, Zhanjiang, Guangdong, China.

den=$1
cpu=$2
duration=$3
k_paths=$4

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

# Output directory.
out_dir="./results"
rm -f -r ./results
mkdir -p $out_dir

trials="trial1 trial2 trial3 trial4 trial5 trial6 trial7 trial8"

# Run experiments.
for tnum in $trials
do
	./run_experiment2.sh $den $cpu $tnum $duration $out_dir $k_paths

done

# Plot results.
sudo python ./plot_results.py --den $den --duration $duration --dir $out_dir
