# Copyright (C) 2019 Huang MaChi at China Mobile Communication
# Corporation, Zhanjiang, Guangdong, China.
# Copyright (C) 2016 Li Cheng at Beijing University of Posts
# and Telecommunications. www.muzixing.com
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

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import Link, Intf, TCLink
from mininet.topo import Topo

import os
import logging
import argparse
import time
import signal
from subprocess import Popen
from multiprocessing import Process

import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import iperf_peers


parser = argparse.ArgumentParser(description="Parameters importation")
parser.add_argument('--den', dest='density', type=int, default=15, help="Host density")
parser.add_argument('--cpu', dest='cpu', type=float, default=2.0, help="Total CPU to allocate to hosts")
parser.add_argument('--duration', dest='duration', type=int, default=60, help="Duration (sec) for each iperf traffic generation")
parser.add_argument('--dir', dest='output_dir', help="Directory to store outputs")
parser.add_argument('--k_paths', dest='kpaths', type=int, default=4, help="Number of alternative paths")
args = parser.parse_args()


class IPMAN(Topo):
	"""
		Class of IPMAN Topology.
	"""
	GZSwitchList = []
	CdnSwitchList = []
	CoreSwitchList = []
	AggSwitchList = []
	EdgeSwitchList = []
	HostList = []
	SerList = []

	def __init__(self, density):
		self.density = density
		self.iGZSwitch = 2
		self.iCdnSwitch = 1
		self.iCoreLayerSwitch = 2
		self.iAggLayerSwitch = 2
		self.iEdgeLayerSwitch = 2
		self.iHost = self.iEdgeLayerSwitch * density
		self.iServer = 3

		# Topo initiation
		Topo.__init__(self)

	def createNodes(self):
		self.createGZSwitch(self.iGZSwitch)
		self.createCdnSwitch(self.iCdnSwitch)
		self.createCoreLayerSwitch(self.iCoreLayerSwitch)
		self.createAggLayerSwitch(self.iAggLayerSwitch)
		self.createEdgeLayerSwitch(self.iEdgeLayerSwitch)
		self.createHost(self.iHost)
		self.createServer(self.iServer)

	def _addSwitch(self, number, level, switch_list):
		"""
			Create switches.
		"""
		for i in xrange(1, number+1):
			PREFIX = str(level) + "00"
			if i >= 10:
				PREFIX = str(level) + "0"
			switch_list.append(self.addSwitch(PREFIX + str(i)))

	def createGZSwitch(self, NUMBER):
		self._addSwitch(NUMBER, 1, self.GZSwitchList)

	def createCdnSwitch(self, NUMBER):
		self._addSwitch(NUMBER, 5, self.CdnSwitchList)

	def createCoreLayerSwitch(self, NUMBER):
		self._addSwitch(NUMBER, 2, self.CoreSwitchList)

	def createAggLayerSwitch(self, NUMBER):
		self._addSwitch(NUMBER, 3, self.AggSwitchList)

	def createEdgeLayerSwitch(self, NUMBER):
		self._addSwitch(NUMBER, 4, self.EdgeSwitchList)

	def createHost(self, NUMBER):
		"""
			Create hosts.
		"""
		for i in xrange(1, NUMBER+1):
			if i >= 100:
				PREFIX = "h"
			elif i >= 10:
				PREFIX = "h0"
			else:
				PREFIX = "h00"
			self.HostList.append(self.addHost(PREFIX + str(i), cpu=args.cpu/float(self.iHost + self.iServer)))

	def createServer(self, NUMBER):
		"""
			Create servers.
		"""
		for i in xrange(1, NUMBER+1):
			if i >= 100:
				PREFIX = "ser"
			elif i >= 10:
				PREFIX = "ser0"
			else:
				PREFIX = "ser00"
			self.SerList.append(self.addHost(PREFIX + str(i), cpu=args.cpu/float(self.iHost + self.iServer)))

	def createLinks(self, bw_gz=10, bw_cdn=10, bw_c2a=10, bw_a2e=10, bw_e2h=10):
		"""
			Add network links.
		"""
		# Servers to Switches
		self.addLink(self.SerList[0], self.GZSwitchList[0], bw=bw_gz, max_queue_size=1000)   # use_htb=False
		self.addLink(self.SerList[1], self.GZSwitchList[1], bw=bw_gz, max_queue_size=1000)   # use_htb=False
		self.addLink(self.SerList[2], self.CdnSwitchList[0], bw=bw_cdn, max_queue_size=1000)   # use_htb=False

		# Edge to Host
		for x in xrange(0, self.iEdgeLayerSwitch):
			for i in xrange(0, self.density):
				self.addLink(
					self.EdgeSwitchList[x],
					self.HostList[self.density * x + i],
					bw=bw_e2h, max_queue_size=1000)   # use_htb=False

		# Core to CDN
		self.addLink(self.CoreSwitchList[0], self.CdnSwitchList[0], bw=bw_cdn, max_queue_size=1000)   # use_htb=False
		self.addLink(self.CoreSwitchList[1], self.CdnSwitchList[0], bw=bw_cdn, max_queue_size=1000)   # use_htb=False

		# GZ to Core
		self.addLink(self.GZSwitchList[0], self.CoreSwitchList[0], bw=bw_gz, max_queue_size=1000)   # use_htb=False
		self.addLink(self.GZSwitchList[1], self.CoreSwitchList[1], bw=bw_gz, max_queue_size=1000)   # use_htb=False

		# Core to Agg
		for i in self.CoreSwitchList:
			for j in self.AggSwitchList:
				self.addLink(i, j, bw=bw_c2a, max_queue_size=1000)   # use_htb=False

		# Agg to Edge
		for i in self.AggSwitchList:
			for j in self.EdgeSwitchList:
				self.addLink(i, j, bw=bw_a2e, max_queue_size=1000)   # use_htb=False

	def set_ovs_protocol_13(self,):
		"""
			Set the OpenFlow version for switches.
		"""
		self._set_ovs_protocol_13(self.GZSwitchList)
		self._set_ovs_protocol_13(self.CdnSwitchList)
		self._set_ovs_protocol_13(self.CoreSwitchList)
		self._set_ovs_protocol_13(self.AggSwitchList)
		self._set_ovs_protocol_13(self.EdgeSwitchList)

	def _set_ovs_protocol_13(self, sw_list):
		for sw in sw_list:
			cmd = "sudo ovs-vsctl set bridge %s protocols=OpenFlow13" % sw
			os.system(cmd)


def set_host_ip(net, topo):
	# Set hosts' IP.
	_hostlist = []
	for k in xrange(len(topo.HostList)):
		_hostlist.append(net.get(topo.HostList[k]))
	i = 1
	j = 1
	for host in _hostlist:
		host.setIP("10.%d.0.%d" % (i, j))
		j += 1
		if j == topo.density+1:
			j = 1
			i += 1

	# Set servers' IP.
	_serverlist = []
	for k in xrange(len(topo.SerList)):
		_serverlist.append(net.get(topo.SerList[k]))
	i = 3
	for server in _serverlist:
		server.setIP("10.%d.0.1" % i)
		i += 1

def install_proactive(net, topo):
	"""
		Install direct flow entries for edge switches.
	"""
	# Edge Switch
	for sw in topo.EdgeSwitchList:
		num = int(sw[-2:])
		# Downstream
		for i in xrange(1, topo.density+1):
			cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
				'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
				nw_dst=10.%d.0.%d,actions=output:%d'" % (sw, num, i, i)
			os.system(cmd)
			cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
				'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
				nw_dst=10.%d.0.%d,actions=output:%d'" % (sw, num, i, i)
			os.system(cmd)
		# Upstream
		cmd = "ovs-ofctl add-group %s -O OpenFlow13 \
			'group_id=1,type=select,bucket=output:16,bucket=output:17'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
			nw_dst=10.3.0.1,actions=group:1'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
			nw_dst=10.3.0.1,actions=group:1'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
			nw_dst=10.4.0.1,actions=group:1'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
			nw_dst=10.4.0.1,actions=group:1'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
			nw_dst=10.5.0.1,actions=group:1'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
			nw_dst=10.5.0.1,actions=group:1'" % sw
		os.system(cmd)

	# GZ Switch
	#1
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.3.0.1,actions=output:1'" % topo.GZSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.3.0.1,actions=output:1'" % topo.GZSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.1.0.0/16, actions=output:2'" % topo.GZSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.1.0.0/16, actions=output:2'" % topo.GZSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.2.0.0/16, actions=output:2'" % topo.GZSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.2.0.0/16, actions=output:2'" % topo.GZSwitchList[0]
	os.system(cmd)

	#2
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.4.0.1,actions=output:1'" % topo.GZSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.4.0.1,actions=output:1'" % topo.GZSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.1.0.0/16, actions=output:2'" % topo.GZSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.1.0.0/16, actions=output:2'" % topo.GZSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.2.0.0/16, actions=output:2'" % topo.GZSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.2.0.0/16, actions=output:2'" % topo.GZSwitchList[1]
	os.system(cmd)

	# CDN Switch
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.5.0.1,actions=output:1'" % topo.CdnSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.5.0.1,actions=output:1'" % topo.CdnSwitchList[0]
	os.system(cmd)

	cmd = "ovs-ofctl add-group %s -O OpenFlow13 \
		'group_id=1,type=select,bucket=output:2,bucket=output:3'" % topo.CdnSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.1.0.0/16,actions=group:1'" % topo.CdnSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.1.0.0/16,actions=group:1'" % topo.CdnSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.2.0.0/16,actions=group:1'" % topo.CdnSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.2.0.0/16,actions=group:1'" % topo.CdnSwitchList[0]
	os.system(cmd)

	# Core Switch
	#1
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.5.0.1,actions=output:1'" % topo.CoreSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.5.0.1,actions=output:1'" % topo.CoreSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.3.0.1,actions=output:2'" % topo.CoreSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.3.0.1,actions=output:2'" % topo.CoreSwitchList[0]
	os.system(cmd)

	cmd = "ovs-ofctl add-group %s -O OpenFlow13 \
		'group_id=1,type=select,bucket=output:3,bucket=output:4'" % topo.CoreSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.1.0.0/16,actions=group:1'" % topo.CoreSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.1.0.0/16,actions=group:1'" % topo.CoreSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.2.0.0/16,actions=group:1'" % topo.CoreSwitchList[0]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.2.0.0/16,actions=group:1'" % topo.CoreSwitchList[0]
	os.system(cmd)

	#2
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.5.0.1,actions=output:1'" % topo.CoreSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.5.0.1,actions=output:1'" % topo.CoreSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.4.0.1,actions=output:2'" % topo.CoreSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.4.0.1,actions=output:2'" % topo.CoreSwitchList[1]
	os.system(cmd)

	cmd = "ovs-ofctl add-group %s -O OpenFlow13 \
		'group_id=1,type=select,bucket=output:3,bucket=output:4'" % topo.CoreSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.1.0.0/16,actions=group:1'" % topo.CoreSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.1.0.0/16,actions=group:1'" % topo.CoreSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
		nw_dst=10.2.0.0/16,actions=group:1'" % topo.CoreSwitchList[1]
	os.system(cmd)
	cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
		'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
		nw_dst=10.2.0.0/16,actions=group:1'" % topo.CoreSwitchList[1]
	os.system(cmd)

	# Agg Switch
	for sw in topo.AggSwitchList:
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
			nw_dst=10.3.0.1,actions=output:1'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
			nw_dst=10.3.0.1,actions=output:1'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
			nw_dst=10.4.0.1,actions=output:2'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
			nw_dst=10.4.0.1,actions=output:2'" % sw
		os.system(cmd)

		cmd = "ovs-ofctl add-group %s -O OpenFlow13 \
			'group_id=1,type=select,bucket=output:1,bucket=output:2'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
			nw_dst=10.5.0.1,actions=group:1'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
			nw_dst=10.5.0.1,actions=group:1'" % sw
		os.system(cmd)

		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
			nw_dst=10.1.0.0/16, actions=output:3'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
			nw_dst=10.1.0.0/16, actions=output:3'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,arp, \
			nw_dst=10.2.0.0/16, actions=output:4'" % sw
		os.system(cmd)
		cmd = "ovs-ofctl add-flow %s -O OpenFlow13 \
			'table=0,idle_timeout=0,hard_timeout=0,priority=10,ip, \
			nw_dst=10.2.0.0/16, actions=output:4'" % sw
		os.system(cmd)


def monitor_devs_ng(fname="./txrate.txt", interval_sec=0.1):
	"""
		Use bwm-ng tool to collect interface transmit rate statistics.
		bwm-ng Mode: rate;
		interval time: 1s.
	"""
	cmd = "sleep 1; bwm-ng -t %s -o csv -u bits -T rate -C ',' > %s" %  (interval_sec * 1000, fname)
	Popen(cmd, shell=True).wait()

def traffic_generation(net, topo, flows_peers):
	"""
		Generate traffics and test the performance of the network.
	"""
	# 1. Start iperf. (Elephant flows)
	# Start the servers.
	serversList = set([peer[0] for peer in flows_peers])
	for server in serversList:
		# filename = server[1:]
		server = net.get(server)
		# server.cmd("iperf -s > %s/%s &" % (args.output_dir, 'server'+filename+'.txt'))
		server.cmd("iperf -s > /dev/null &" )   # Its statistics is useless, just throw away.

	time.sleep(3)

	# Start the clients.
	for src, dest in flows_peers:
		server = net.get(src)
		client = net.get(dest)
		# filename = src[1:]
		# client.cmd("iperf -c %s -t %d > %s/%s &" % (server.IP(), args.duration, args.output_dir, 'client'+filename+'.txt'))
		client.cmd("iperf -c %s -t %d > /dev/null &" % (server.IP(), 1990))   # Its statistics is useless, just throw away. 1990 just means a great number.
		time.sleep(3)

	# Wait for the traffic turns stable.
	time.sleep(10)

	# 2. Start bwm-ng to monitor throughput.
	monitor = Process(target = monitor_devs_ng, args = ('%s/bwmng.txt' % args.output_dir, 1.0))
	monitor.start()

	# 3. The experiment is going on.
	time.sleep(args.duration + 5)

	# 4. Shut down.
	monitor.terminate()
	os.system('killall bwm-ng')
	os.system('killall iperf')

def run_experiment(density, ip="192.168.56.101", port=6653, bw_gz=23.2, bw_cdn=26.1, bw_c2a=3.3, bw_a2e=10, bw_e2h=1):
	"""
		Firstly, start up Mininet;
		secondly, start up Ryu controller;
		thirdly, generate traffics and test the performance of the network.
	"""
	# Create Topo.
	topo = IPMAN(density)
	topo.createNodes()
	topo.createLinks(bw_gz=bw_gz, bw_cdn=bw_cdn, bw_c2a=bw_c2a, bw_a2e=bw_a2e, bw_e2h=bw_e2h)

	# 1. Start Mininet.
	CONTROLLER_IP = ip
	CONTROLLER_PORT = port
	net = Mininet(topo=topo, link=TCLink, controller=None, autoSetMacs=True)
	net.addController(
		'controller', controller=RemoteController,
		ip=CONTROLLER_IP, port=CONTROLLER_PORT)
	net.start()

	# Set the OpenFlow version for switches as 1.3.0.
	topo.set_ovs_protocol_13()
	# Set the IP addresses for hosts and servers.
	set_host_ip(net, topo)
	# Install proactive flow entries.
	install_proactive(net, topo)
	
	# For debugging
	# CLI(net)

	# 2. Start the controller.
	# Controller_Ryu = Popen("ryu-manager --observe-links ./IPMAN/IPMAN.py --k_paths=%d --weight=bw" % args.kpaths, shell=True, preexec_fn=os.setsid)

	# Wait until the controller has discovered network topology.
	# time.sleep(60)

	# 3. Generate traffics and test the performance of the network.
	traffic_generation(net, topo, iperf_peers.iperf_peers)

	# Stop the controller.
	# os.killpg(Controller_Ryu.pid, signal.SIGKILL)

	# Stop Mininet.
	net.stop()

if __name__ == '__main__':
	setLogLevel('info')
	if os.getuid() != 0:
		logging.warning("You are NOT root!")
	elif os.getuid() == 0:
		# run the experiment
		run_experiment(args.density)
