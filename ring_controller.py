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
        links = [(link.src.dpid, link.dst.dpid, link.src.port_no) for link in links_list]
	global contatore_TD
	global contatore_SF
	print(switches)
	print(links)
	contatore_TD = ( contatore_TD + 1 )
	print("TD :")
	print(contatore_TD)
	
	if contatore_TD == contatore_SF: #quando ha finito il topology discovery
		sw_id = 1
		#inizializzo matrice per instradamento [colonne: sw_id, cw_src_port, ccw_src_port, host, host_ip]
		routing_matrix = [[0 for col_links_matrix in range(5)] for row_links_matrix in range(len(switches))]
		for i in switches: #for da i cicli per i switch [i=1->6]
			sw_id_locked = sw_id
			for link in links: #for per scorrere tutti i link trovati dal TD
				if (link[0] == sw_id_locked and (link[1] == routing_matrix[i-2][0] or i == 1)):
					routing_matrix[i-1][2] = link[2]
				if (link[0] == sw_id and sw_id == sw_id_locked and (link[1] != routing_matrix[i-2][0] or i == 1)):
					routing_matrix[i-1][0] = sw_id
					routing_matrix[i-1][1] = link[2]
					sw_id = link[1]
					
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


        
	
	
	
	# ciclo for su matrice uscita dal topology discovery

        	# def send_flow_mod(self, datapath)

		# modifica group table
		def send_group_mod(self, datapath):
		    ofp = datapath.ofproto
		    ofp_parser = datapath.ofproto_parser

		    port_cw = #tab[i][1]
		    port_ccw = #tab[i][2]
		    #max_len = 2000
		    actions_norm = [ofp_parser.OFPActionOutput(port_cw)]
		    actions_fault = [ofp_parser.OFPActionOutput(port_ccw)]

		    weight = 100
		    #watch_port = #tab[i][1]
		    #watch_group = 0
		    buckets_1 = [ofp_parser.OFPBucket(weight, watch_port="""tab[i][1]""", actions_norm),
				    ofp_parser.OFPBucket(weight, watch_port="""tab[i][2]""", actions_fault)]

		    buckets_2 = [ofp_parser.OFPBucket(weight, watch_port="""tab[i][2]""", actions_fault),
				    ofp_parser.OFPBucket(weight, watch_port="""tab[i][1]""", """no actions == drop""")]

		    #group_id = 1
		    #group_id = 2
		    req_1 = ofp_parser.OFPGroupMod(datapath, ofp.OFPGC_ADD,
						 ofp.OFPGT_FF, group_id = 1, buckets_1)
		    req_2 = ofp_parser.OFPGroupMod(datapath, ofp.OFPGC_ADD,
						 ofp.OFPGT_FF, group_id = 2, buckets_2)

		    datapath.send_msg(req_1, req_2)
