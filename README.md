# Description:

This tool collects all the selfips from bigip partitions, which are lbaas agent environment_prefixed, from the targeted bigip host.

It validates the selfips with 'local-<device_name>-' and the vlan with 'vlan-'.

Then it updates neutron selfip port mac by using MAC Selfip map.

# Usage:
```bash
python main.py --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/services/f5/f5-openstack-agent.ini --host-ip 10.145.64.180 --user admin --password default --nodebug --dry-run
```

* `--config-file /etc/neutron/neutron.conf`: neutron configuration file.

* `--config-file /etc/neutron/services/f5/f5-openstack-agent.ini`: lbaas agent configuration file.

* `--host-ip 10.145.64.180`: target bigip host.

* `--user admin`: bigip username.

* `--password default`: bigip password.

* `--nodebug`: no debug log mode.

* `--dry-run`: enable dry run mode
