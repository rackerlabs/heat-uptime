#!/usr/bin/env python

import ConfigParser
import argparse
import logging
import os
import requests
import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from keystoneclient.v2_0.client import Client as keystone_client
from heatclient.client import Client as heat_client
from statsd import StatsClient

requests.packages.urllib3.disable_warnings()


def time_build_info(username, password, tenant, auth_url, heat_url, region):
    keystone = keystone_client(username=username, password=password,
                               tenant_name=tenant, auth_url=auth_url)
    token = keystone.auth_token
    heat = heat_client('1', endpoint=heat_url, region_name=region, token=token)
    statsd = StatsClient()

    with statsd.timer('uptime.{}'.format(region)):
        heat.build_info.build_info()


def main():
    log_handler = logging.StreamHandler(sys.stdout)
    logging.getLogger('apscheduler.executors.default').addHandler(log_handler)

    parser = argparse.ArgumentParser(description='Get uptime metrics')
    parser.add_argument('-c', '--config', help='Path to config file',
                        default='/etc/heat-uptime/uptime.cfg')
    args = parser.parse_args()
    config_file = args.config

    config = ConfigParser.ConfigParser()
    try:
        config.read(config_file)
    except IOError:
        print('Config file {} does not exist'.format(config_file))
        sys.exit(1)

    scheduler = BackgroundScheduler()

    auth_url = config.get('DEFAULT', 'auth_url')
    interval = int(config.get('DEFAULT', 'interval'))

    for section in config.sections():
        username = config.get(section, 'username')
        password = config.get(section, 'password')
        tenant = config.get(section, 'tenant')
        heat_url = config.get(section, 'heat_url')
        region = section

        scheduler.add_job(time_build_info, 'interval', [username, password,
                          tenant, auth_url, heat_url, region],
                          seconds=interval, name=region)

    scheduler.start()
    while True:
        try:
            pass
        except KeyboardInterrupt:
            scheduler.shutdown()
            sys.exit(0)


if __name__ == '__main__':
    main()
