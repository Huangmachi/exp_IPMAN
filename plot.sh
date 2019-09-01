#!/bin/bash
# Copyright (C) 2016 Huang MaChi at Chongqing University
# of Posts and Telecommunications, China.

den=$1
duration=60
out_dir='./results'

sudo python ./plot_results.py --den $den --duration $duration --dir $out_dir
