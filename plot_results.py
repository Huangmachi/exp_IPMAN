# Copyright (C) 2019 Huang MaChi at China Mobile Communication
# Corporation, Zhanjiang, Guangdong, China.
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
import re
import numpy as np
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(description="Plot results")
parser.add_argument('--den', dest='density', type=int, default=15, help="Host density")
parser.add_argument('--duration', dest='duration', type=int, default=60, help="Duration (sec) for each iperf traffic generation")
parser.add_argument('--dir', dest='out_dir', help="Directory to store outputs")
args = parser.parse_args()


def read_file_1(file_name, delim=','):
	"""
		Read the bwmng.txt file.
	"""
	read_file = open(file_name, 'r')
	lines = read_file.xreadlines()
	lines_list = []
	for line in lines:
		line_list = line.strip().split(delim)
		lines_list.append(line_list)
	read_file.close()

	# Remove the last second's statistics, because they are mostly not intact.
	last_second = lines_list[-1][0]
	_lines_list = lines_list[:]
	for line in _lines_list:
		if line[0] == last_second:
			lines_list.remove(line)

	return lines_list

def read_file_2(file_name):
	"""
		Read the first_packets.txt and successive_packets.txt file.
	"""
	read_file = open(file_name, 'r')
	lines = read_file.xreadlines()
	lines_list = []
	for line in lines:
		if line.startswith('rtt') or line.endswith('ms\n'):
			lines_list.append(line)
	read_file.close()
	return lines_list

def calculate_average(value_list):
	average_value = sum(map(float, value_list)) / len(value_list)
	return average_value

def get_throughput(full_bisection_bw, throughput, traffic, app, input_file):
	"""
		csv output format:
		(Type rate)
		unix_timestamp;iface_name;bytes_out/s;bytes_in/s;bytes_total/s;bytes_in;bytes_out;packets_out/s;packets_in/s;packets_total/s;packets_in;packets_out;errors_out/s;errors_in/s;errors_in;errors_out\n
		(Type svg, sum, max)
		unix timestamp;iface_name;bytes_out;bytes_in;bytes_total;packets_out;packets_in;packets_total;errors_out;errors_in\n
		The bwm-ng mode used is 'rate'.

		throughput = {
						'trial1':
						{
							'realtime_bisection_bw': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'realtime_throughput': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'accumulated_throughput': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'normalized_total_throughput': {'IPMAN':x%, 'SDIPMAN':x%, ...}
						},
						'trial2':
						{
							'realtime_bisection_bw': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'realtime_throughput': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'accumulated_throughput': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'normalized_total_throughput': {'IPMAN':x%, 'SDIPMAN':x%, ...}
						},
						...
					}
	"""
	lines_list = read_file_1(input_file)
	first_second = int(lines_list[0][0])
	column_bytes_out_rate = 2   # bytes_out/s
	column_bytes_out = 6   # bytes_out

	if app == 'NonBlocking':
		switch = '1001'
	elif app in ['IPMAN', 'SDIPMAN']:
		switch = '4[0-9][0-9][0-9]'
	else:
		pass
	sw = re.compile(switch)

	if not throughput.has_key(traffic):
		throughput[traffic] = {}

	if not throughput[traffic].has_key('realtime_bisection_bw'):
		throughput[traffic]['realtime_bisection_bw'] = {}
	if not throughput[traffic].has_key('realtime_throughput'):
		throughput[traffic]['realtime_throughput'] = {}
	if not throughput[traffic].has_key('accumulated_throughput'):
		throughput[traffic]['accumulated_throughput'] = {}
	if not throughput[traffic].has_key('normalized_total_throughput'):
		throughput[traffic]['normalized_total_throughput'] = {}

	if not throughput[traffic]['realtime_bisection_bw'].has_key(app):
		throughput[traffic]['realtime_bisection_bw'][app] = {}
	if not throughput[traffic]['realtime_throughput'].has_key(app):
		throughput[traffic]['realtime_throughput'][app] = {}
	if not throughput[traffic]['accumulated_throughput'].has_key(app):
		throughput[traffic]['accumulated_throughput'][app] = {}
	if not throughput[traffic]['normalized_total_throughput'].has_key(app):
		throughput[traffic]['normalized_total_throughput'][app] = 0

	for i in xrange(args.duration + 1):
		if not throughput[traffic]['realtime_bisection_bw'][app].has_key(i):
			throughput[traffic]['realtime_bisection_bw'][app][i] = 0
		if not throughput[traffic]['realtime_throughput'][app].has_key(i):
			throughput[traffic]['realtime_throughput'][app][i] = 0
		if not throughput[traffic]['accumulated_throughput'][app].has_key(i):
			throughput[traffic]['accumulated_throughput'][app][i] = 0

	for row in lines_list:
		iface_name = row[1]
		if iface_name not in ['total', 'lo', 'eth0', 'enp0s3', 'enp0s8', 'docker0']:
			if switch == '4[0-9][0-9][0-9]':
				if sw.match(iface_name):
					_port = int(iface_name.split('eth')[-1])
					if int(_port) <= args.density:   # Choose down-going interfaces only.
						if (int(row[0]) - first_second) <= args.duration:   # Take the good values only.
							throughput[traffic]['realtime_bisection_bw'][app][int(row[0]) - first_second] += float(row[column_bytes_out_rate]) * 8.0 / (10 ** 6)   # Mbit/s
							throughput[traffic]['realtime_throughput'][app][int(row[0]) - first_second] += float(row[column_bytes_out]) * 8.0 / (10 ** 6)   # Mbit
					else:
						pass
			elif switch == '1001':   # Choose all the interfaces. (For NonBlocking Topo only)
				if sw.match(iface_name):
					if (int(row[0]) - first_second) <= args.duration:
						throughput[traffic]['realtime_bisection_bw'][app][int(row[0]) - first_second] += float(row[column_bytes_out_rate]) * 8.0 / (10 ** 6)   # Mbit/s
						throughput[traffic]['realtime_throughput'][app][int(row[0]) - first_second] += float(row[column_bytes_out]) * 8.0 / (10 ** 6)   # Mbit
			else:
				pass

	for i in xrange(args.duration + 1):
		for j in xrange(i+1):
			throughput[traffic]['accumulated_throughput'][app][i] += throughput[traffic]['realtime_throughput'][app][j]   # Mbit

	throughput[traffic]['normalized_total_throughput'][app] = throughput[traffic]['accumulated_throughput'][app][args.duration] / (full_bisection_bw * args.duration)   # percentage

	return throughput

def get_value_list_1(throughput, traffic, item, app):
	"""
		Get the values from the "throughput" data structure.
	"""
	value_list = []
	for i in xrange(args.duration + 1):
		value_list.append(throughput[traffic][item][app][i])
	return value_list

def get_average_bisection_bw(throughput, traffics, app):
	complete_list = []
	for traffic in traffics:
		complete_list.append(throughput[traffic]['accumulated_throughput'][app][args.duration] / float(args.duration))
	return complete_list

def get_value_list_2(value_dict, traffics, item, app):
	"""
		Get the values from the  data structure.
	"""
	complete_list = []
	for traffic in traffics:
		complete_list.append(value_dict[traffic][item][app])
	return complete_list

def get_utilization(utilization, traffic, app, input_file):
	"""
		Get link utilization and link bandwidth utilization.
	"""
	lines_list = read_file_1(input_file)
	first_second = int(lines_list[0][0])
	column_packets_out = 11   # packets_out
	column_packets_in = 10   # packets_in
	column_bytes_out = 6   # bytes_out
	column_bytes_in = 5   # bytes_in

	if not utilization.has_key(traffic):
		utilization[traffic] = {}
	if not utilization[traffic].has_key(app):
		utilization[traffic][app] = {}

	for row in lines_list:
		iface_name = row[1]
		if iface_name.startswith('2'):
			if (int(row[0]) - first_second) <= args.duration:   # Take the good values only.
				if not utilization[traffic][app].has_key(iface_name):
					utilization[traffic][app][iface_name] = {'LU_out':0, 'LU_in':0, 'LBU_out':0, 'LBU_in':0}
				# if int(row[11]) > 2:
				if row[6] not in ['0', '60', '120']:
					utilization[traffic][app][iface_name]['LU_out'] = 1
				# if int(row[10]) > 2:
				if row[5] not in ['0', '60', '120']:
					utilization[traffic][app][iface_name]['LU_in'] = 1
				utilization[traffic][app][iface_name]['LBU_out'] += int(row[6])
				utilization[traffic][app][iface_name]['LBU_in'] += int(row[5])
		elif iface_name.startswith('3'):
			_port = int(iface_name.split('eth')[-1])
			if _port > 2:   # Choose Down-going interfaces only.
				if (int(row[0]) - first_second) <= args.duration:   # Take the good values only.
					if not utilization[traffic][app].has_key(iface_name):
						utilization[traffic][app][iface_name] = {'LU_out':0, 'LU_in':0, 'LBU_out':0, 'LBU_in':0}
					# if int(row[11]) > 2:
					if row[6] not in ['0', '60', '120']:
						utilization[traffic][app][iface_name]['LU_out'] = 1
					# if int(row[10]) > 2:
					if row[5] not in['0', '60', '120']:
						utilization[traffic][app][iface_name]['LU_in'] = 1
					utilization[traffic][app][iface_name]['LBU_out'] += int(row[6])
					utilization[traffic][app][iface_name]['LBU_in'] += int(row[5])
		else:
			pass

	return utilization

def get_link_utilization_ratio(utilization, traffics, app):
	num_list = []
	complete_list = []
	for traffic in traffics:
		num = 0
		for interface in utilization[traffic][app].keys():
			if utilization[traffic][app][interface]['LU_out'] == 1:
				num += 1
			if utilization[traffic][app][interface]['LU_in'] == 1:
				num += 1
		num_list.append(num)
		complete_list.append(float(num) / (len(utilization[traffic][app].keys()) * 2))
	return complete_list

def get_value_list_3(utilization, traffic, app):
	"""
		Get link bandwidth utilization ratio.
	"""
	value_list = []
	link_bandwidth_utilization = {}
	utilization_list = []
	for i in np.linspace(0, 1, 101):
		link_bandwidth_utilization[i] = 0

	for interface in utilization[traffic][app].keys():
		_port = int(interface.split('eth')[-1])
		if interface.startswith('3'):
			if _port <= 2:
				_link_bandwidth = 3.3
			elif _port > 2:
				_link_bandwidth = 10
			else:
				pass
		elif interface.startswith('2'):
			if _port == 1:
				_link_bandwidth = 26.1
			elif _port == 2:
				_link_bandwidth = 23.2
			elif _port > 2:
				_link_bandwidth = 3.3
			else:
				pass
		else:
			pass
		
		ratio_out = float(utilization[traffic][app][interface]['LBU_out'] * 8) / (_link_bandwidth * (10 ** 6) * args.duration)
		ratio_in = float(utilization[traffic][app][interface]['LBU_in'] * 8) / (_link_bandwidth * (10 ** 6) * args.duration)
		utilization_list.append(ratio_out)
		utilization_list.append(ratio_in)

	for ratio in utilization_list:
		for seq in link_bandwidth_utilization.keys():
			if ratio <= seq:
				link_bandwidth_utilization[seq] += 1

	for seq in link_bandwidth_utilization.keys():
		link_bandwidth_utilization[seq] = float(link_bandwidth_utilization[seq]) / len(utilization_list)

	for seq in sorted(link_bandwidth_utilization.keys()):
		value_list.append(link_bandwidth_utilization[seq])

	return value_list

def plot_results():
	"""
		Plot the results:
		1. Plot average bisection bandwidth
		2. Plot normalized total throughput
		3. Plot link utilization ratio
		4. Plot link bandwidth utilization ratio

		throughput = {
						'trial1':
						{
							'realtime_bisection_bw': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'realtime_throughput': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'accumulated_throughput': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'normalized_total_throughput': {'IPMAN':x%, 'SDIPMAN':x%, ...}
						},
						'trial2':
						{
							'realtime_bisection_bw': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'realtime_throughput': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'accumulated_throughput': {'IPMAN':{0:x, 1:x, ..}, 'SDIPMAN':{0:x, 1:x, ..}, ...},
							'normalized_total_throughput': {'IPMAN':x%, 'SDIPMAN':x%, ...}
						},
						...
					}
	"""
	full_bisection_bw = 1.0 * args.density * 2   # (unit: Mbit/s)
	_traffics = "trial1 trial2 trial3 trial4 trial5 trial6 trial7 trial8"
	traffics = _traffics.split(' ')
	apps = ['IPMAN', 'SDIPMAN']
	throughput = {}
	utilization = {}

	for traffic in traffics:
		for app in apps:
			bwmng_file = args.out_dir + '/%s/%s/bwmng.txt' % (traffic, app)
			throughput = get_throughput(full_bisection_bw, throughput, traffic, app, bwmng_file)
			utilization = get_utilization(utilization, traffic, app, bwmng_file)

	# 1. Plot average throughput.
	fig = plt.figure()
	fig.set_size_inches(10, 5)
	num_groups = len(traffics)
	num_bar = len(apps)
	IPMAN_value_list = get_average_bisection_bw(throughput, traffics, 'IPMAN')
	SDIPMAN_value_list = get_average_bisection_bw(throughput, traffics, 'SDIPMAN')
	index = np.arange(num_groups) + 0.15
	bar_width = 0.13
	plt.bar(index, IPMAN_value_list, bar_width, color='g', label='IPMAN')
	plt.bar(index + 1 * bar_width, SDIPMAN_value_list, bar_width, color='r', label='SDIPMAN')
	plt.xticks(index + num_bar / 2.0 * bar_width, traffics, fontsize='small')
	plt.ylabel('Average Throughput\n(Mbps)', fontsize='x-large')
	plt.ylim(0, full_bisection_bw)
	plt.yticks(np.linspace(0, full_bisection_bw, 11))
	plt.legend(loc='upper right', ncol=len(apps), fontsize='small')
	plt.grid(axis='y')
	plt.tight_layout()
	plt.savefig(args.out_dir + '/1.average_throughput.png')

	# 2. Plot normalized total throughput.
	item = 'normalized_total_throughput'
	fig = plt.figure()
	fig.set_size_inches(10, 5)
	num_groups = len(traffics)
	num_bar = len(apps)
	IPMAN_value_list = get_value_list_2(throughput, traffics, item, 'IPMAN')
	SDIPMAN_value_list = get_value_list_2(throughput, traffics, item, 'SDIPMAN')
	index = np.arange(num_groups) + 0.15
	bar_width = 0.13
	plt.bar(index, IPMAN_value_list, bar_width, color='g', label='IPMAN')
	plt.bar(index + 1 * bar_width, SDIPMAN_value_list, bar_width, color='r', label='SDIPMAN')
	plt.xticks(index + num_bar / 2.0 * bar_width, traffics, fontsize='small')
	plt.ylabel('Normalized Total Throughput\n', fontsize='x-large')
	plt.ylim(0, 1)
	plt.yticks(np.linspace(0, 1, 11))
	plt.legend(loc='upper right', ncol=len(apps), fontsize='small')
	plt.grid(axis='y')
	plt.tight_layout()
	plt.savefig(args.out_dir + '/2.normalized_total_throughput.png')

	# 3. Plot link utilization ratio.
	fig = plt.figure()
	fig.set_size_inches(10, 5)
	num_groups = len(traffics)
	num_bar = len(apps)
	IPMAN_value_list = get_link_utilization_ratio(utilization, traffics, 'IPMAN')
	SDIPMAN_value_list = get_link_utilization_ratio(utilization, traffics, 'SDIPMAN')
	index = np.arange(num_groups) + 0.15
	bar_width = 0.15
	plt.bar(index, IPMAN_value_list, bar_width, color='g', label='IPMAN')
	plt.bar(index + 1 * bar_width, SDIPMAN_value_list, bar_width, color='r', label='SDIPMAN')
	plt.xticks(index + num_bar / 2.0 * bar_width, traffics, fontsize='small')
	plt.ylabel('Link utilization Ratio\n', fontsize='x-large')
	plt.ylim(0, 1.2)
	plt.yticks(np.linspace(0, 1.2, 13))
	plt.legend(loc='upper right', ncol=len(apps), fontsize='small')
	plt.grid(axis='y')
	plt.tight_layout()
	plt.savefig(args.out_dir + '/3.link_utilization_ratio.png')

	# 4. Plot link bandwidth utilization ratio.
	fig = plt.figure()
	fig.set_size_inches(12, 16)
	num_subplot = len(traffics)
	num_raw = 4
	num_column = 2
	NO_subplot = 1
	x = np.linspace(0, 1, 101)
	for i in xrange(len(traffics)):
		plt.subplot(num_raw, num_column, NO_subplot)
		y1 = get_value_list_3(utilization, traffics[i], 'IPMAN')
		y2 = get_value_list_3(utilization, traffics[i], 'SDIPMAN')
		plt.plot(x, y1, 'g-', linewidth=2, label="IPMAN")
		plt.plot(x, y2, 'r-', linewidth=2, label="SDIPMAN")
		plt.title('%s' % traffics[i], fontsize='xx-large')
		plt.xlabel('Link Bandwidth Utilization Ratio', fontsize='large')
		plt.xlim(0, 1)
		plt.xticks(np.linspace(0, 1, 11))
		plt.ylabel('CDF of Link Bandwidth\nUtilization Ratio', fontsize='x-large')
		plt.ylim(0, 1)
		plt.yticks(np.linspace(0, 1, 11))
		plt.legend(loc='lower right', fontsize='large')
		plt.grid(True)
		NO_subplot += 1
	plt.tight_layout()
	plt.savefig(args.out_dir + '/4.link_bandwidth_utilization_ratio.png')


if __name__ == '__main__':
	plot_results()
