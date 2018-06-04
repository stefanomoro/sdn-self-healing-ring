from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.term import makeTerm
import sys

if '__main__' == __name__:

	args = str(sys.argv[1])
	print (args)
	num = int(args)
	
	net = Mininet(controller=RemoteController)
	c0 = net.addController('c0', port=6633)

	switches = []
	for i in range(int(num)) :
		str_s = 's' + str(i+1)
		str_h = 'h' + str(i+1)
		temp_s = net.addSwitch(str_s)
		temp_h = net.addHost(str_h)
		net.addLink(temp_s , temp_h)
		switches.append(  temp_s )
	for i in range(len(switches) - 1):
		net.addLink(switches[i],switches[i + 1])
	net.addLink(switches[0],switches[-1])
	net.build()
	for s in switches:
		s.start([c0])

	net.startTerms()

	CLI(net)
	net.stop()

