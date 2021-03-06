import time
import os
import sys
import re

import requests
from requests.exceptions import ConnectionError
import boto.ec2
from docker import Client


def get_container_id():
    with open('/proc/self/cgroup') as f:
        lines = f.read().split('\n')

    cid = lines[0].split('/')[-1]
    if cid.startswith('docker'):
        cid = re.findall('docker-(.*)\.scope', cid)[0]
    return cid


CID = get_container_id()


def check_docker_sock():
    if not os.path.exists('/var/run/docker.sock'):
        print('Cannot see the Docker socket file, aborting')
        sys.exit(-1)


def get_containers():
    cli = Client(base_url='unix://var/run/docker.sock')
    cli.containers()
    return [cont for cont in cli.containers() if cont['Id'] != CID]


def get_ec2_info():
    root = 'http://169.254.169.254/latest/meta-data/'
    try:
        zone = requests.get('%s/placement/availability-zone' % root).text
        region = zone[:-1]
        instance_id = requests.get('%s/instance-id' % root).text
    except ConnectionError:
        print('Cannot reach EC2, aborting')
        sys.exit(-1)

    return {'zone': zone, 'region': region, 'id': instance_id}


def terminate_instance(region, instance_id):
    conn = boto.ec2.connect_to_region(region)
    conn.terminate_instances(instance_ids=[instance_id])


ONE_HOUR = 3600
SLEEP_TIME = 60
check_docker_sock()
print('Container ID: %s' % get_container_id())
ec2_info = get_ec2_info()
print(ec2_info)

start = time.time()
print('Watching...')


while True:
    containers = get_containers()

    if containers == []:
        idling_since = time.time() - start

        if idling_since < ONE_HOUR:
            print('Nothing is happening since %s seconds' % idling_since)
        else:
            print('Idling for one hour, killing it')
            terminate_instance(ec2_info['region'], ec2_info['id'])
    else:
        start = time.time()

    time.sleep(SLEEP_TIME)
