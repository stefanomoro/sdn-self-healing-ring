from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
contatore_SF = 0
contatore_TD = 0

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
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]
	global contatore_TD
	global contatore_SF
	print(switches)
	print(links)
	contatore_TD = ( contatore_TD + 1 )
	print("TD :")
	print(contatore_TD)
	if contatore_TD == contatore_SF: #quando ha finito il topology discovery
		sw_id = 1
		routing_matrix = [[0 for col_links_matrix in range(5)] for row_links_matrix in range(len(switches))] #inizializzo matrice per instradamento [colonne: sw_id, cw_dest ccw_dest, host, host_ip]
		for i in switches: #for da i cicli per i switch
			for link in links: #for per scorrere tutti i link trovati dal TD
				if (links[link][0] == sw_id and (links[link][1] != routing_matrix[i-1][0] or i == 0)):
					routing_matrix[i][0] = sw_id
					routing_matrix[i][1] = links[link][2]
					sw_id = links[link][1]
					break
		print(routing_matrix)
					
				
				
			
			
	
	
	
	

    #utilizzando un approccio proattivo non ce ne frega di mandare i pacchetti al controller
    #dunque dobbiamo definire delle regole di default ---> group table (group type FAST FAILOVER)
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def set_default_rule(self, ev):
	global contatore_SF
	contatore_SF = contatore_SF + 1
	print("SF :")
	print(contatore_SF)
        # install default forwarding rule
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser


        #bisogna trovare la sintassi per definire bene come vogliamo la group table (fast failover)
        """ Group table setup """
        buckets = []

        # Action Bucket: <PWD port_i , SetState(i-1)
        for port in range():
            dest_ip = self.int_to_ip_str(port)
            dest_eth = self.int_to_mac_str(port)
            dest_tcp = (port) * 100
            actions = [ofparser.OFPActionOutput(port=port)]

            buckets.append(ofparser.OFPBucket(weight=100,
                                              watch_port=ofproto.OFPP_ANY,
                                              watch_group=ofproto.OFPG_ANY,
                                              actions=actions))

        req = ofparser.OFPGroupMod(datapath=datapath,
                                   command=ofproto.OFPGC_ADD,
                                   type_=ofproto.OFPGT_SELECT,
                                   group_id=1,
                                   buckets=buckets)

        datapath.send_msg(req)
