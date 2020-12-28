import logging
import os
import time

import googleapiclient.discovery

compute = googleapiclient.discovery.build('compute', 'v1')


def start_instance(project, zone, instance_name):
    res = compute.instances().start(
        project=project,
        zone=zone,
        instance=instance_name
    ).execute()
    logging.info(f"Start instance response: {res}")
    return res


def launch(request, context):
    project = os.environ['BUDGET_PROJECT']
    zone = os.environ['BUDGET_ZONE']
    instance = os.environ['BUDGET_INSTANCE']

    time.sleep(40)
    start_instance(project, zone, instance)
