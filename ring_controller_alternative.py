from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

topoOk = False

class switch(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(switch,self).__init__(*args,**kwargs)
		#self.mac_to_port = {}

	#topology discovery --> restituisce una lista di switch e una lista di link con edges e porta di inoltro da src
	#NB: bisogna probabilmente aggiungere delle funzioni che si accorgano di eventuali cambiamenti della topologia
	@set_ev_cls(event.EventSwitchEnter)
	def get_topology_data(self, ev):
		switch_list = get_switch(self, None)
		switches = [switch.dp.id for switch in switch_list]
		links_list = get_link(self, None)
		links = [(link.src.dpid, link.dst.dpid, link.src.port_no) for link in links_list]
		
		print("SWITCHES"),
		print(switches)
		print("LINKS"),
		print(links)

		global topoOk

		if not topoOk and isRing(switches,links) : 
			
			routing_matrix = []

			for sw in switches: 
				sw_links = [link for link in links if link[0] == sw]

				#sw_links[0][0] e' uguale a sw
				sw_ccw = [x for x in routing_matrix if sw == x.id_cw] 	#cerco se c'e' gia salvato un sw (ccw rispetto a me)
				sw_cw = [x for x in routing_matrix if sw == x.id_ccw]	#cerco anche per l'altro senso

				if sw_ccw:	#check se c'e' switch gia salvato con id_cw il mio id
					if sw_ccw[0].id == sw_links[0][1]:
						routing_matrix.append(ringNode(sw, sw_links[1][1], sw_links[0][1], sw_links[1][2], sw_links[0][2],"","") )
					else:	#altrimenti e' il contrario
						routing_matrix.append(ringNode(sw, sw_links[0][1], sw_links[1][1], sw_links[0][2], sw_links[1][2],"","") )
				
				elif sw_cw:	
					if sw_cw[0].id == sw_links[0][1]:
						routing_matrix.append(ringNode(sw, sw_links[0][1], sw_links[1][1], sw_links[0][2], sw_links[1][2],"","") )
					else:	
						routing_matrix.append(ringNode(sw, sw_links[1][1], sw_links[0][1], sw_links[1][2], sw_links[0][2],"","") )
				else:	#se non ho trovato altro allora e' nuovo
					routing_matrix.append(ringNode(sw, sw_links[0][1], sw_links[1][1], sw_links[0][2], sw_links[1][2],"","") )

			
			topoOk = True
			printMat(routing_matrix)
			print("______");
					

class ringNode(object):
    id = ""
    id_cw = ""
    id_ccw = ""
    port_cw = ""
    port_ccw = ""
    host_port = ""
    host_ip = ""
    # The class "constructor" - It's actually an initializer 
    def __init__(self, id, id_cw, id_ccw, port_cw, port_ccw, host_port, host_ip):
        self.id = id
        self.id_cw = id_cw
        self.id_ccw = id_ccw
        self.port_cw = port_cw
        self.port_ccw = port_ccw
        self.host_port = host_port
    	self.host_ip = host_ip


def printMat(mat):
	for sw in mat:
		print("id:"),
		print(sw.id),
		print(" id_cw:"),
		print(sw.id_cw),
		print(" id_ccw:"),
		print(sw.id_ccw),
		print(" port_cw:"),
		print(sw.port_cw),
		print(" port_ccw:"),
		print(sw.port_ccw)


def isRing(switches,links):

	for sw in switches:
		sw_links = [x for x in links if x[0] == sw]

		if len(sw_links) < 2 or not [x for x in sw_links for y in links if x[1] == y[0]]:
			return False
	return True