# -*- coding: utf-8 -*-

import options

from db import queries
from ve_client import init_bigip
from os_client import neutron_client

from oslo_log import log as logging

import resource_helper
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from pprint import pprint

# from os_client import neutron_client

LOG = logging.getLogger(__name__)
conf = options.conf

logging.setup(conf, "Vlan MAC Migrate")

def enable_dryrun():
    return conf.dry_run

# def get_db_client():
#   return queries.Queries()

def get_bigip_client():
    return init_bigip()

def get_neutron_client():
    return neutron_client

def get_environment_prefix():
    if conf.environment_prefix:
        partition_prefix = conf.environment_prefix + '_'
    else:
        raise Exception("Cannot found partition prefix")
    return partition_prefix

def get_partitions(bigip):
    helper = None
    ret = []

    helper = resource_helper.BigIPResourceHelper(
        resource_helper.ResourceType.folder)
    partition_objs = helper.get_resources(bigip)
    prefix = get_environment_prefix()

    return [ptn.name for ptn in partition_objs
            if ptn.name.startswith(prefix)]

def get_partition_selfips(bigip, partition):
    helper = None
    ret = []

    helper = resource_helper.BigIPResourceHelper(
        resource_helper.ResourceType.selfip
    )
    selfip_objs = helper.get_resources(
        bigip, partition=partition)

    return selfip_objs

def validated_selfips(selfips):
    ret = []
    prefix = 'local-' + bigip.device_name + '-'

    ret = [ip for ip in selfips
           if ip.name.startswith(prefix)]

    return ret

def get_ve_selfips(bigip):
    ret = []
    ptns = get_partitions(bigip)

    print("\ngether and format selfip port info in partitions %s from device %s" 
          % (ptns, bigip.device_name))
    for ptn in ptns:
        selfip_objs = get_partition_selfips(bigip, ptn)
        ret.extend(selfip_objs)

    ret = validated_selfips(ret)
    return ret

def fmt_vlan_selfips(selfip_objs):
    ret = {}

    for selfip in selfip_objs:
        vlan = selfip.vlan
        name = selfip.name

        if not ret.get(vlan, []):
            ret[vlan] = [name]
        else:
            ret[vlan].append(name)

    return ret

def _valid_vlan_name(name):
    if 'vlan-' in name:
        return True
    False

def get_vlan_mac(bigip, partition, name):
    helper = resource_helper.BigIPResourceHelper(
        resource_helper.ResourceType.vlan)
    stat_keys = ['macTrue']

    stats = helper.get_stats(
        bigip, partition=partition,
        name=name, stat_keys=stat_keys
    )
    mac = stats['macTrue']

    return mac

def fmt_mac_selfips(bigip, vlan_selfips):
    ret = {}

    for k, v in vlan_selfips.items():
        ptn, vlan = k.split("/")[1:]

        if _valid_vlan_name(vlan):
            mac_key = get_vlan_mac(
                bigip, ptn, vlan
            )
            ret[mac_key] = v

    return ret

def _log_notfound_port(db_ports, ve_port_names):
    db_port_names = [port['name'] for port in db_ports]

    # NOTE: this is not possible by using ve selfip port to find port in db.
    # the port is in db, but not in ve.
    # ve_port_notfound = set(db_port_names) - set(ve_port_names)

    # the port is in ve, but not in db.
    db_port_notfound = set(ve_port_names) - set(db_port_names)

    # ve_notfound.extend(list(ve_port_notfound))
    db_notfound.extend(list(db_port_notfound))

def update_mac(mac, port):

    port_bind_porfile = port['binding:profile']
    local_link_info = port_bind_porfile['local_link_information']
    info = local_link_info[0]
    node_vtep_ip = info.get("node_vtep_ip")

    # NOTE: if network without vtep? use the default mac???
    # if node_vtep_ip:
        # info['lb_mac'] = 'test_pzhang'
    info['lb_mac'] = mac
    port_id = port['id']
    patch = {'port':{'binding:profile': port_bind_porfile}}

    print("\n update port %s" % port['name'])
    pprint(patch)
    if not enable_dryrun():
        port = neutron_cli.update_port(port_id, patch)

def update_selfip_ports(mac_selfips):

    print("\nsearch port and update selfip ports 'lb_mac'")
    for mac, port_names in mac_selfips.items():
        ports = neutron_cli.list_ports(name=port_names)
        ports = ports.get("ports", [])

        _log_notfound_port(ports, port_names)

        for port in ports:
            update_mac(mac, port)


if __name__ == "__main__":
    """
    this tool collects all the selfips in lbaas agent
    environment_prefixed partitions of the targeted bigip host.

    validate the selfips with 'local-<device_name>-'
    validate the vlan with 'vlan-'

    update neutron selfip port mac by using mac selfip map.
    only the ports with vtep ip will be updated.
    """
    start = time.time()

    # ve_notfound = []
    db_notfound = []

    print("\ncollecting and processing info, please wait.")

    # gether mac-selfips map from bigips
    bigip = get_bigip_client()
    selfip_objs = get_ve_selfips(bigip)
    vlan_selfips = fmt_vlan_selfips(selfip_objs)
    mac_selfips = fmt_mac_selfips(bigip, vlan_selfips)

    print("\n------ we will update these Vlan Seflips ------")
    pprint(vlan_selfips)

    print("\n------ we will update these MACs for Neutron Port ------")
    pprint(mac_selfips)

    # according to the mac-selfips map to update neutron ports
    neutron_cli = get_neutron_client()
    if enable_dryrun():
        print("\nConfiguration will NOT issued, in dry run mode.")
    update_selfip_ports(mac_selfips)

    # print("------ these ports cannot be found in Bigip VE ------")
    # pprint(ve_notfound)
    print("\n------ these ports cannot be found in Neutron DB ------")
    pprint(db_notfound)

    end = time.time()
    elapse = end - start
    print("\nFinish update selfip port for BigIP %s. Time elapse %s second" % (bigip.hostname, elapse))
