import logging
import time


def promote_ephemeral_ip(
        compute,
        project,
        region,
        ephemeral_ip,
        address_name,
        subnetwork):
    config = {
        "addressType": "INTERNAL",
        "address": ephemeral_ip,
        "name": address_name,
        "subnetwork": subnetwork
    }
    logging.debug(f'Promoting IP with config: {config}')
    res = compute.addresses().insert(
        project=project,
        region=region,
        body=config).execute()
    logging.debug(f'Ephemeral IP {ephemeral_ip} promoted. Response: {res}')
    return res


def create_static_ip(compute, project, region, static_ip_name):
    config = {
        'name': static_ip_name
    }
    compute.addresses().insert(
        project=project,
        region=region,
        body=config).execute()

    time.sleep(3)

    req = compute.addresses().get(
        project=project,
        region=region,
        address=static_ip_name)
    res = req.execute()
    logging.debug(f'Static IP {static_ip_name} created with response: {res}')
    return res
