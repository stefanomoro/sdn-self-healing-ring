# ...
#  		# RECUPERIAMO DAI METADATI DEL PACCHETTO
#       # la porta di ingresso allo switch
#         in_port = msg.match['in_port']
#         dpid = datapath.id
# 		# msg.data contiene il pacchetto in caratteri
#         pkt = packet.Packet(msg.data)
#       # get_protocol ci restituisce le intestazioni del protocollo
#         eth = pkt.get_protocol(ethernet.ethernet)
# 		# ethernet non nullo
#         assert eth is not None
#       # destinazione e sorgente
#         dst = eth.dst
#         src = eth.src
# 		# porta in ingresso sorgente
#         self.mac_to_port[dpid][src] = in_port
# ...

# FUNZIONE MODIFICA FLOW_TABLE
def send_flow_mod(self, datapath):
    ofp = datapath.ofproto
    ofp_parser = datapath.ofproto_parser
    
    # IMPOSTO REGOLE FLOW_TABLE 0 (sono dubbioso)	
	# porta per host
	out_port = routing_matrix[i][3]		
	match = parser.OFPMatch(eth_dst=dst, ipv4_dst=routing_matrix[i][4])
	# output verso l'host
	actions = 
	[			   
		parser.OFPActionOutput(ofp.OFPP_LOCAL, out_port)	
	]
	# applico azioni e vado a tabella successiva
	inst = 
	[
		parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions), parser.OFPInstructionGotoTable(1)  
	]
	req = parser.OFPFlowMod(datapath=datapath, table_id=0, priority=0, match=match, instructions=inst)
	
	# devo trovare un modo per non inoltrarlo due volte con flag o contatori (o traffic monitor?)
	# IMPOSTO REGOLE FLOW_TABLE 1	
	# broadcast		
	match = parser.OFPMatch(in_port=routing_matrix[i][1], eth_dst='ff:ff:ff:ff:ff:ff')
	actions = 
	[			   
		parser.OFPActionOutput(ofp.OFPP_FLOOD)	# per ora lascio flood
	]
	# applico azioni e vado a tabella successiva
	inst = 
	[
		parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions), parser.OFPInstructionGotoTable(2)  
	]
	req = parser.OFPFlowMod(datapath=datapath, table_id=1, priority=0, match=match, instructions=inst)
	
	# IMPOSTO REGOLE FLOW_TABLE 2
	# broadcast		
	match = parser.OFPMatch(in_port=routing_matrix[i][2], eth_dst='ff:ff:ff:ff:ff:ff')
	actions = 
	[			   
		parser.OFPActionOutput(ofp.OFPP_FLOOD)	# per ora lascio flood
	]
	# applico azioni e vado a tabella successiva
	inst = 
	[
		parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions), parser.OFPInstructionGotoTable(3) 
	]
	req = parser.OFPFlowMod(datapath=datapath, table_id=2, priority=0, match=match, instructions=inst)
	
	# IMPOSTO REGOLE FLOW_TABLE 3
	# mando a group table 1
	match = parser.OFPMatch(in_port=routing_matrix[i][1])
	# vado a tabella successiva
	inst = 
	[
		parser.OFPInstructionGotoTable(group 1), parser.OFPInstructionGotoTable(4)
	]
	req = parser.OFPFlowMod(datapath=datapath, table_id=3, priority=0, match=match, instructions=inst)
	
	# IMPOSTO REGOLE FLOW_TABLE 4
	# mando a group table 2
	match = parser.OFPMatch(in_port=routing_matrix[i][2])
	# vado a tabella successiva
	inst = 
	[
		parser.OFPInstructionGotoTable(group 2)
	]
	req = parser.OFPFlowMod(datapath=datapath, table_id=4, priority=0, match=match, instructions=inst)
	