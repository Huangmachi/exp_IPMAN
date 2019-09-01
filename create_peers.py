# Copyright (C) 2016 Huang MaChi at Chongqing University
# of Posts and Telecommunications, Chongqing, China.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import random


parser = argparse.ArgumentParser(description="IPMAN experiments")
parser.add_argument('--den', dest='density', type=int, default=15, help="Host density")
args = parser.parse_args()


def create_hostlist(num):
	"""
		Create hosts list.
	"""
	hostlist = []
	for i in xrange(1, num+1):
		if i >= 100:
			PREFIX = "h"
		elif i >= 10:
			PREFIX = "h0"
		else:
			PREFIX = "h00"
		hostlist.append(PREFIX + str(i))
	return hostlist

def create_peers():
	"""
		Create iperf host peers and write to a file.
	"""
	flows_peers = []
	host_num = args.density * 2
	HostList = create_hostlist(host_num)

	for host in HostList:
		prob = random.random()
		if prob < 0.28:
			flows_peers.append((host, 'ser001'))
		elif prob < 0.56:
			flows_peers.append((host, 'ser002'))
		else:
			flows_peers.append((host, 'ser003'))

	# Shuffle the sequence of the flows_peers.
	random.shuffle(flows_peers)

	# Write flows_peers into a file for reuse.
	file_save = open('iperf_peers.py', 'w')
	file_save.write('iperf_peers=%s' % flows_peers)
	file_save.close()

if __name__ == '__main__':
	create_peers()
