# -*- coding: utf-8 -*-

import options

from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client

conf = options.conf

auth = identity.Password(
    auth_url=conf.service_auth.auth_url,
    username=conf.service_auth.admin_user,
    password=conf.service_auth.admin_password,
    project_name=conf.service_auth.admin_tenant_name
)

sess = session.Session(auth=auth)

if not conf.service_auth.region:
    print("\n***** NOTE: CANNOT find region configuration in neutron.conf ******")

neutron_client = client.Client(
    session=sess, region_name=conf.service_auth.region)
