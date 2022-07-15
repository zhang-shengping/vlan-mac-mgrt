# f5-ct-limit-migrate工具主要修改两点：1. 旧的 vip connection limit 设置为 lb flavor 对映的 connection limit 值2. 旧的 vs connection limit 设置为 0`python main.py --config-file /etc/neutron/services/f5/f5-openstack-agent.ini --config-file /etc/neutron/neutron.conf --host-ip 110.114.73.244 --f5-agent 6c383d85-d4f2-47cf-88a7-301213ba3985`参数说明：* --config-file /etc/neutron/neutron.conf: 当前 neutron 配置文件。* --config-file /etc/neutron/service/f5/f5-openstack-agent.ini: 当前 F5 agent provider 配置文件。* --f5-agent 7c6a4b8e-7d9a-40fe-b55e-c3516d24f3e9: 当前 F5 agent ID。* --host-ip 110.115.71.57: 当前 F5 agent provider 控制的其中一台 bigip host 地址，如果有多台，需要多次运行迁移命令。* --dry-run: 用于数据构建测试，注意此测试不会真正下发任何配置，不会对 Neutron DB 和 F5 BigIP 设备做任何更改。