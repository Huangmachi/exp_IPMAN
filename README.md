## exp_IPMAN

exp_IPMAN is an experiment to compare the performance of the IP Metropolitan Area Network of China Mobile Communication Corporation while adopting ECMP, BGP and SDN.


### Prerequisites

The following softwares should have been installed in your Ubuntu machine.
* Mininet: git clone git://github.com/mininet/mininet; mininet/util/install.sh -a
* Ryu: git clone git://github.com/osrg/ryu.git; cd ryu; pip install .
* bwm-ng: apt-get install bwm-ng
* Networkx: pip install networkx
* Numpy: pip install numpy
* Matplotlib: apt-get install python-matplotlib


### Make some change

To register parsing parameters, you need to add the following code into the end of ryu/ryu/flags.py.

    CONF.register_cli_opts([
        # k_shortest_forwarding
        cfg.IntOpt('k_paths', default=4, help='number of candidate paths of KSP.'),
        cfg.StrOpt('weight', default='bw', help='weight type of computing shortest path.'),
        cfg.IntOpt('fanout', default=4, help='switch fanout number.')])


### Reinstall Ryu

You must reinstall Ryu, so that you can run the new code. In the top directory of Ryu project:

    sudo python setup.py install


### Start

Note: Before doing the experiment, you should change the controller's IP address from '192.168.56.101' to your own machine's eth0 IP address in the fattree.py module in each application, because '192.168.56.101' is my computer's eth0 IP address (Try 'ifconfig' in your Ubuntu to find out the eth0's IP address). Otherwise, the switches can't connect to the controller.

Just start it as follows, you will find the results in the 'results' directory.

    $ ./run_experiment.sh 15 2.0 60 4

The first parameter '15' means there are 15 users under each Edge Switch; the second parameter '2.0' means the total CPUs allocated to the hosts; the third parameter '60' means each experimental traffic will last for 60 seconds; the last parameter '4' means the SDN controller chooses the ultimate path from 4 best paths. It will take you about 1 hour to complete the experiment.


### Author

Brought to you by Huang MaChi (China Mobile Communication Corporation, Zhanjiang, Guangdong, China).

If you have any question, you can email me at huangmachi@foxmail.com.  Don't forget to STAR this repository!

Enjoy it!
