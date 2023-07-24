# -*- coding: utf-8 -*-

from f5.bigip import ManagementRoot
from options import conf

def init_bigip():
    host = conf.host_ip
    user = conf.user
    password = conf.password
    bigip = ManagementRoot(host, user, password)

    device_name = get_device_name(bigip)
    if not device_name:
        raise Exception("Cannot found device name for host %s" % host)
    bigip.device_name = device_name

    return bigip


def get_device_name(bigip):
    devices = bigip.tm.cm.devices.get_collection()
    if not devices:
        return
    for device in devices:
        if conf.host_ip == device.managementIp:
            return device.name
