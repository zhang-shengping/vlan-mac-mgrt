# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from oslo_config import cfg
import sys
from oslo_db.options import database_opts
from f5_openstack_agent.lbaasv2.drivers.bigip.opts import \
    OPTS as f5_opts


tool_opts = [
    cfg.StrOpt("host-ip",
               short="ip",
               default="",
               help=("Provide VE host ip")),

    cfg.StrOpt("user",
               short="u",
               default="",
               help=("Provid VE admin username")),

    cfg.StrOpt("password",
               short="p",
               default="",
               help=("Provider VE admin password")),

    cfg.BoolOpt("dry-run",
                short="dr",
                default=False,
                help=("Run for test"))
]

auth_opts = [
    cfg.StrOpt(
            'auth_url',
            help=_('Authentication endpoint'),
        ),
    cfg.StrOpt(
            'admin_user',
            default='admin',
            help=_('The service admin user name'),
        ),
    cfg.StrOpt(
            'admin_tenant_name',
            default='admin',
            help=_('The service admin tenant name'),
        ),
    cfg.StrOpt(
            'admin_password',
            secret=True,
            default='password',
            help=_('The service admin password'),
        ),
    cfg.StrOpt(
            'admin_user_domain',
            default='admin',
            help=_('The admin user domain name'),
        ),
    cfg.StrOpt(
            'admin_project_domain',
            default='admin',
            help=_('The admin project domain name'),
        ),
    cfg.StrOpt(
            'region',
            # default='RegionOne',
            default='',
            help=_('The deployment region'),
        ),
    cfg.StrOpt(
            'service_name',
            default='lbaas',
            help=_('The name of the service'),
        ),
    cfg.StrOpt(
            'auth_version',
            default='3',
            help=_('The auth version used to authenticate'),
        ),
    cfg.StrOpt(
            'endpoint_type',
            default='public',
            help=_('The endpoint_type to be used')
        ),
    cfg.BoolOpt(
            'insecure',
            default=False,
            help=_('Disable server certificate verification')
        )
]

conf = cfg.CONF

# set tool cli opts
conf.register_cli_opts(tool_opts)

# set lbaas agent opts
conf.register_opts(f5_opts)

# set neutron db opts
conf.register_opts(database_opts, group='database')

# set neutron server client opts
conf.register_opts(auth_opts, 'service_auth')

def parse_options(args=sys.argv[1:],
              # conf=cfg.CONF,
              project="vlan-mac-mgrt"):
    cfg.CONF(args, project)
    return cfg.CONF

parse_options()

if __name__ == "__main__":
    print("\n----- Neutron client OPTS -----")
    print("auth_url: " +  conf.service_auth.auth_url)
    print("admin_user: " + conf.service_auth.admin_user)
    print("admin_password: " + conf.service_auth.admin_password)
    print("admin_tenant: " + conf.service_auth.admin_tenant_name)
    print("region: " + conf.service_auth.region)

    print("\n----- Neutron DB OPTS -----")
    print("DB connection: " + conf.database.connection)

    print("\n----- VE client OPTS -----")
    print("host ip: " + conf.host_ip)
    print("user: " + conf.user)
    print("password: " + conf.password)

    print("\n----- iControl OPTS -----")
    print("environment prefix: " + conf.environment_prefix)
