#!/usr/bin/env python

# Copyright 2015 Google Inc. All Rights Reserved.
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


import logging


def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None


def create_instance(compute, project, zone, static_ip, instance_name,
                    machine_type, startup_script, shutdown_script,
                    preemptible, requirements_content,
                    docker_template_content, docker_compose_content,
                    nginx_conf_content):
    # Get the latest Debian Jessie image.
    image_response = compute.images().getFromFamily(
        project='cos-cloud', family='cos-85-lts').execute()
    source_disk_image = image_response['selfLink']

    # Configure the machine
    machine_type_full = f"zones/{zone}/machineTypes/{machine_type}"

    config = {
        'name': instance_name,
        'machineType': machine_type_full,

        'scheduling': {'preemptible': preemptible},

        'tags': {
            'items': [
                'http-server',
                'https-server'
            ]
        },
        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'diskSizeGb': '100',
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT',
                 'natIP': static_ip}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write',
                'https://www.googleapis.com/auth/cloud-platform'
            ]
        }],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [
                {
                    # Startup script is automatically executed on startup
                    'key': 'startup-script',
                    'value': startup_script
                },
                {
                    # Shutdown script is automatically executed on shutdown.
                    'key': 'shutdown-script',
                    'value': shutdown_script
                },
                {
                    'key': 'REQUIREMENTS',
                    'value': requirements_content
                },
                {
                    'key': 'DOCKER_TEMPLATE',
                    'value': docker_template_content,
                },
                {
                    'key': 'DOCKER_COMPOSE_TEMPLATE',
                    'value': docker_compose_content
                },
                {
                    'key': 'NGINX_CONF_TEMPLATE',
                    'value': nginx_conf_content,
                }
            ]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()


def delete_instance(compute, project, zone, name):
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()


def get_instance(compute, project, zone, instance_name):
    res = compute.instances().get(
        project=project,
        zone=zone,
        instance=instance_name
    ).execute()
    logging.debug(f"Get instance response: {res}")
    return res
