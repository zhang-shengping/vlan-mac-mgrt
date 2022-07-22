# -*- coding: utf-8 -*-

import eventlet
eventlet.monkey_patch()

import netaddr
import queries
import options
import constant
import requests
from oslo_config import cfg
from oslo_log import log as logging

from f5.bigip import ManagementRoot
import resource_helper
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from os_client import neutron_client

LOG = logging.getLogger(__name__)
options.load_options()
options.parse_options()
conf = cfg.CONF

logging.setup(conf, "ConnectionLimitMigrate")

agent_id = conf.f5_agent
host_ip = conf.host_ip
db_query = queries.Queries()

if conf.environment_prefix:
    partition_prefix = conf.environment_prefix + '_'
else:
    raise Exception("Cannot found partition prefix")

def get_device_name(host, device_list):
    if not device_list:
        return
    for device in device_list:
        if host == device.managementIp:
            return device.name

def init_bigip(host, user, passwd):
    bigip = ManagementRoot(host, user, passwd)
    devices = bigip.tm.cm.devices.get_collection()
    device_name = get_device_name(host, devices)
    if not device_name:
        raise Exception("Cannot found device name for host %s" % host)
    bigip.device_name = device_name
    return bigip

def resource_tree(agent_id):
    tree = {agent_id: dict()}
    agent_resource = tree[agent_id]

    loadbalancers = db_query.get_loadbalancers_by_agent_id(agent_id)

    for lb in loadbalancers:
        if lb.project_id not in agent_resource:
            agent_resource[lb.project_id] = [lb]
        else:
            agent_resource[lb.project_id] += [lb]

    return agent_resource

def modify_ctlimit(agent_id, bigip):
    vs_helper = resource_helper.BigIPResourceHelper(
        resource_helper.ResourceType.virtual)

    tenant_resources = resource_tree(agent_id)

    for tenant_id, lbs in tenant_resources.items():
        partition = partition_name(tenant_id)

        partition_vips = get_partition_vips(partition, lbs)

        update_vip_limit(partition_vips)

        partition_vss = vs_helper.get_resources(
            bigip, partition=partition)

        vs_limit = 0
        update_vs_limit(partition_vss, partition_vips, partition, vs_limit)

def update_vip_limit(vips):
    if len(vips) != 0:

       pool = eventlet.greenpool.GreenPool()
       for item in vips.values():
           vip = item['vip']
           vip_limit = item['ct_limit']
           LOG.info(
               "Refresh connection limit %s for virtual address %s of "
               " partition %s." % (vip_limit, vip.name, vip.partition)
           )
           try:
               if not DRYRUN:
                   pool.spawn(vip.modify, connectionLimit=vip_limit)
           except Exception as ex:
               LOG.error(
                   "Fail to refresh virtual address %s"
                   " connection limit %s." % (vs.name, vip_limit)
               )
               raise ex
       pool.waitall()



def get_partition_vips(partition, lbs):

    vip_helper = resource_helper.BigIPResourceHelper(
        resource_helper.ResourceType.virtual_address)

    def fetch(lb):
        name = vip_name(lb.id)
        vip = vip_helper.load(
            bigip,
            partition=partition,
            name=name
        )

        ct_limit  = constant.FLAVOR_CONN_MAP[str(lb.flavor)]['connection_limit']

        ip_version = netaddr.IPAddress(lb.vip_address).version

        if vip is None:
            raise Exception("Cannot get vip %s in partition %s" % (name, partition))
        if ct_limit is None:
            raise Exception("Cannot get vip %s flavor %s connection limit" % (name, lb.flavor))
        if ip_version is None:
            raise Exception("Cannot vip_address from lb %s" % (name))

        if ip_version == 4:
            rate_limit = 32
        if ip_version == 6:
            rate_limit = 128

        return {"vip": vip, "ct_limit": ct_limit, "rt_limit": rate_limit}


    partition_vips = {}
    pool = eventlet.greenpool.GreenPool()
    for result in pool.imap(fetch, lbs):
        name = result['vip'].name
        partition_vips[name] = result

    return partition_vips

def get_vs_rt_limit(vips, vs):
    vip_name  = vs.destination.split('/')[2].split(':')[0]

    if vip_name not in vips:
        raise Exception(
            "The vip_name %s cannot be found in vips %s" % (
                vip_name, vips
            )
        )
    return vips[vip_name]['rt_limit']


def update_vs_limit(vss, vips, partition, limit):
    if len(vss) != 0:
       pool = eventlet.greenpool.GreenPool()
       for vs in vss:
           try:
               rt_limit = get_vs_rt_limit(vips, vs)
               LOG.info(
                   "Modify vs %s, connection limit %s, rate limit %s" % (
                   vs.name, limit, rt_limit)
               )
               if not DRYRUN:
                   pool.spawn(vs.modify, connectionLimit=limit, rateLimitDstMask=rt_limit)
           except Exception as ex:
               LOG.error(
                   "Fail to refresh virtual server %s"
                   " connection limit %s." % (vs.name, limit)
               )
               raise ex
       pool.waitall()


def partition_name(tenant_id):
    if tenant_id is not None:
        name = partition_prefix + tenant_id
    else:
        name = "Common"
    return name

def vip_name(lb_id):
    name = partition_prefix + lb_id
    return name

if __name__ == "__main__":
    DRYRUN=conf.dry_run
    bigip = init_bigip(host_ip, conf.icontrol_username, conf.icontrol_password)

    a = requests.adapters.HTTPAdapter(pool_maxsize=1)
    bigip.icrs.session.mount('https://', a)

    start = time.time()
    modify_ctlimit(agent_id, bigip)
    end = time.time()
    elapse = end - start
    LOG.info("Finish migrating for BigIP %s. Time elapse %s" % (bigip.hostname, elapse))

