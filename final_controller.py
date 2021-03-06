from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ether_types
from ryu.lib.packet import arp
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link, get_all_host


routing_matrix = []
topoOk = False
hostOk = False
i = 0


class switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(switch, self).__init__(*args, **kwargs)

    # Effettuo il topology discovery di links e switches
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self, None)
        switches = [switch.dp.id for switch in switch_list]
        links_list = get_link(self, None)
        links = [(link.src.dpid, link.dst.dpid, link.src.port_no) for link in links_list]
        print("\n---------------------")
        print("Added switch id => "),
        print(switch.dp.id)
        print("link status => "),
        print(links)
        print("---------------------\n")
        global routing_matrix
        global topoOk
        if not topoOk and isRing(switches, links):
            # routing_matrix = []
            for sw in switches:
                sw_links = [link for link in links if link[0] == sw]
                # sw_links[0][0] e' uguale a sw
                sw_ccw = [x for x in routing_matrix if
                          sw == x.id_cw]  # cerco se c'e' gia salvato un sw (ccw rispetto a me)
                sw_cw = [x for x in routing_matrix if sw == x.id_ccw]  # cerco anche per l'altro senso
                if sw_ccw:  # check se c'e' switch gia salvato con id_cw il mio id
                    if sw_ccw[0].id == sw_links[0][1]:
                        routing_matrix.append(
                            ringNode(sw, sw_links[1][1], sw_links[0][1], sw_links[1][2], sw_links[0][2], "", "", 0))

                    else:  # altrimenti e' il contrario
                        routing_matrix.append(
                            ringNode(sw, sw_links[0][1], sw_links[1][1], sw_links[0][2], sw_links[1][2], "", "", 0))

                elif sw_cw:
                    if sw_cw[0].id == sw_links[0][1]:
                        routing_matrix.append(
                            ringNode(sw, sw_links[0][1], sw_links[1][1], sw_links[0][2], sw_links[1][2], "", "", 0))
                    else:
                        routing_matrix.append(
                            ringNode(sw, sw_links[1][1], sw_links[0][1], sw_links[1][2], sw_links[0][2], "", "", 0))
                else:  # se non ho trovato altro allora e' nuovo
                    routing_matrix.append(
                        ringNode(sw, sw_links[0][1], sw_links[1][1], sw_links[0][2], sw_links[1][2], "", "", 0))
            topoOk = True
            print("\n---------------------\nRouting Matrix Completed\n")
            printMat(routing_matrix)
            print("---------------------\n")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # installiamo la default miss entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        dpid = datapath.id
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        arp_in = pkt.get_protocol(arp.arp)

        # installo le tabelle dopo aver acquisito tutti gli host
        global hostOk
        global routing_matrix
        sw = [x for x in routing_matrix if x.id == dpid]
        sw_obj = sw[0]
        if hostOk and not sw_obj.installed:  # and non ho ancora installato la tabella su dpid

            # prendendo i riferimenti dall'oggetto switch che matcha l'id compilo flow e group tables
            # poi set flag di avvenuta installazione (cosi la prossima volta evito di reinstallare)
            self.group_mod(datapath, sw_obj.port_cw, sw_obj.port_ccw)
            self.flow_mod(datapath, sw_obj)

            # set flag di installazione avvenuta
            idx = 0
            for s in routing_matrix:
                if s.id == sw_obj.id:
                    routing_matrix[idx].installed = 1
                    break
                idx += 1

            print("\n---------------------")
            print("Tables installed on switch", dpid)
            print("---------------------\n")

        # gestione centralizzata arp
        if arp_in is not None:
            assert arp_in.opcode == arp.ARP_REQUEST
            print("\n---------------------")
            print("ARP packet from DP id-> ", dpid, "SRC mac->",eth.src)
            print("---------------------\n")
            destination_host_mac = None
            host_list = get_all_host(self)
            for host in host_list:
                if arp_in.dst_ip in host.ipv4:
                    destination_host_mac = host.mac
                    break

            # aggiungo host a routing matrix
            global i
            # if i < len(routing_matrix):
            if i < 3:
                for host in host_list:
                    for sw in routing_matrix:
                        if host.port.dpid == sw.id and sw.host_mac is "":
                            sw.host_mac = host.mac
                            sw.host_port = int(host.port.name[-1])
                            i += 1

            # elif not hostOk and i == len(routing_matrix):
            elif not hostOk and i == 3:
                hostOk = True
                print("\n---------------------")
                print("Discover all hosts")
                printMat(routing_matrix)
                print("---------------------\n")

            # host non trovato
            if destination_host_mac is None:
                return
            pkt_out = packet.Packet()
            eth_out = ethernet.ethernet(
                dst=eth.src,
                src=destination_host_mac,
                ethertype=ether_types.ETH_TYPE_ARP
            )
            arp_out = arp.arp(
                opcode=arp.ARP_REPLY,
                src_mac=destination_host_mac,
                src_ip=arp_in.dst_ip,
                dst_mac=arp_in.src_mac,
                dst_ip=arp_in.src_ip
            )
            pkt_out.add_protocol(eth_out)
            pkt_out.add_protocol(arp_out)
            pkt_out.serialize()
            actions = [
                parser.OFPActionOutput(
                    in_port
                )
            ]
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=ofproto.OFPP_CONTROLLER,
                actions=actions,
                data=pkt_out.data
            )
            datapath.send_msg(out)

        else:
            return

    # definisco la funzione che compila la flow table
    def flow_mod(self, datapath, sw):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        table_id = 0

        # inoltro da porta cw
        match = ofp_parser.OFPMatch(in_port=sw.port_ccw)
        actions = [ofp_parser.OFPActionGroup(1)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                 actions)]
        req2 = ofp_parser.OFPFlowMod(datapath, table_id, ofp.OFPFC_ADD,
                                     priority=1, match=match, instructions=inst)
        datapath.send_msg(req2)

        # inoltro da porta ccw
        match = ofp_parser.OFPMatch(in_port=sw.port_cw)
        actions = [ofp_parser.OFPActionOutput(sw.port_ccw)]
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                 actions)]
        req3 = ofp_parser.OFPFlowMod(datapath, table_id, ofp.OFPFC_ADD,
                                     priority=1, match=match, instructions=inst)
        datapath.send_msg(req3)

        if sw.host_mac is not "":
            # inoltro all'host
            match = ofp_parser.OFPMatch(eth_dst=sw.host_mac)
            actions = [ofp_parser.OFPActionOutput(sw.host_port)]
            inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                     actions)]
            req1 = ofp_parser.OFPFlowMod(datapath, table_id, ofp.OFPFC_ADD,
                                         priority=3, match=match, instructions=inst)
            datapath.send_msg(req1)

            # inoltro da porta host
            match = ofp_parser.OFPMatch(in_port=sw.host_port)
            actions = [ofp_parser.OFPActionGroup(2)]
            inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                                     actions)]
            req4 = ofp_parser.OFPFlowMod(datapath, table_id, ofp.OFPFC_ADD,
                                         priority=1, match=match, instructions=inst)
            datapath.send_msg(req4)

            # manda ARP al controllore
            match = ofp_parser.OFPMatch(in_port=sw.host_port, eth_type=0x0806)
            actions = [ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
            inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
            req5 = ofp_parser.OFPFlowMod(datapath=datapath, priority=2, match=match, instructions=inst)
            datapath.send_msg(req5)

    # definisco la funzione che compila la group table
    def group_mod(self, datapath, cw, ccw):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        # group id che gestisce i pacchetti in senso orario
        actions_norm = [ofp_parser.OFPActionOutput(cw)]
        actions_fault = [ofp_parser.OFPActionOutput(ofp.OFPP_IN_PORT)]
        buckets_1 = [ofp_parser.OFPBucket(watch_port=cw, actions=actions_norm),
                     ofp_parser.OFPBucket(watch_port=ccw, actions=actions_fault)]
        req_1 = ofp_parser.OFPGroupMod(datapath, ofp.OFPGC_ADD,
                                       ofp.OFPGT_FF, group_id=1, buckets=buckets_1)
        datapath.send_msg(req_1)

        # group id che gestisce i pacchetti dall'host
        actions_fault_host = [ofp_parser.OFPActionOutput(ccw)]
        buckets_2 = [ofp_parser.OFPBucket(watch_port=cw, actions=actions_norm),
                     ofp_parser.OFPBucket(watch_port=ccw, actions=actions_fault_host)]
        req_2 = ofp_parser.OFPGroupMod(datapath, ofp.OFPGC_ADD,
                                       ofp.OFPGT_FF, group_id=2, buckets=buckets_2)
        datapath.send_msg(req_2)


class ringNode(object):
    id = ""
    id_cw = ""
    id_ccw = ""
    port_cw = ""
    port_ccw = ""
    host_port = ""
    host_mac = ""
    installed = ""

    # The class "constructor" - It's actually an initializer
    def __init__(self, id, id_cw, id_ccw, port_cw, port_ccw, host_port, host_mac, installed):
        self.id = id
        self.id_cw = id_cw
        self.id_ccw = id_ccw
        self.port_cw = port_cw
        self.port_ccw = port_ccw
        self.host_port = host_port
        self.host_mac = host_mac
        self.installed = installed


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
        print(" host_port:"),
        print(sw.host_port)
        print(" host_mac:"),
        print(sw.host_mac)
        print(" installed:"),
        print(sw.installed)


def isRing(switches, links):
    for sw in switches:
        sw_links = [x for x in links if x[0] == sw]
        if len(sw_links) < 2 or not [x for x in sw_links for y in links if x[1] == y[0]]:
            return False
    return True