from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link


class switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(switch,self).__init__(*args,**kwargs)
        # self.mac_to_port = {}

    # topology discovery --> restituisce una lista di switch e una lista di link con edges e porta di inoltro da src
    # provare ad aggiungere host discovery
    # NB: può anche essere messo nel decoratore switch features (fonte: verticale)
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self, None)
        switches = [switch.dp.id for switch in switch_list]
        links_list = get_link(self, None)
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]


    # funzione che crea la matrice di routing


    # l'evento switchfeatures è generato dallo switch nel momento dell'accensione
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    #definisco la funzione che compila la group table, la richiamo nel ciclo for che scorre la routing matrix
    def send_group_mod(self, datapath, cw, ccw):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        port_cw = cw
        port_ccw = ccw
        # max_len = 2000
        actions_norm = [ofp_parser.OFPActionOutput(port_cw)]
        actions_fault = [ofp_parser.OFPActionOutput(port_ccw)]

        weight = 100
        # watch_port = #tab[i][1]
        # watch_group = 0
        buckets_1 = [ofp_parser.OFPBucket(weight, watch_port= cw, actions=actions_norm),
                     ofp_parser.OFPBucket(weight, watch_port= ccw, actions=actions_fault)]

        buckets_2 = [ofp_parser.OFPBucket(weight, watch_port= ccw, actions=actions_fault),
                     ofp_parser.OFPBucket(weight, watch_port= cw, """no actions == drop""")]

        # group_id = 1
        # group_id = 2
        req_1 = ofp_parser.OFPGroupMod(datapath, ofp.OFPGC_ADD,
                                       ofp.OFPGT_FF, group_id=1, buckets=buckets_1)
        req_2 = ofp_parser.OFPGroupMod(datapath, ofp.OFPGC_ADD,
                                       ofp.OFPGT_FF, group_id=2, buckets=buckets_2)

        datapath.send_msg([req_1, req_2])

    #definisco la funzione che compila le flow table, la richiamo nel ciclo for che scorre la routing matrix
    # def send_flow_mod


    #installo le tabelle sugli switch
    def switch_features_handler(self,ev):
        datapath = ev.msg.datapath #qui dovrebbero esserci info sullo switch
        #ofproto = datapath.ofproto
        #parser = datapath.ofproto_parser

            # send_flow_mod(self, datapath, ....)
            # send_group_mod(self, datapath, cw, ccw)

    # PROBLEMA: ogni volta che uno switch si manifesta viene eseguito il codice con il datapath corretto (perchè viene preso
    # dal messaggio mandato dallo switch), ma le funzioni di creazione delle table hanno bisogno anche dei dati sulle porte
    # che sono disponibili solo se il topology discovery è completato e se il datapath viene correttamente associato alle
    # righe della routing matrix
