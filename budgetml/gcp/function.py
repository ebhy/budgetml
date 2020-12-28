import logging
import os
import zipfile
from tempfile import TemporaryFile

import googleapiclient.discovery
import requests

from budgetml import orchestrator
from budgetml.gcp.pubsub import create_topic

service = googleapiclient.discovery.build('cloudfunctions', 'v1')
cloud_functions_api = service.projects().locations().functions()


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            if file != '__init__.py':
                ziph.write(os.path.join(root, file), file)


def create_upload_url(parent):
    upload_url = \
        cloud_functions_api.generateUploadUrl(parent=parent,
                                              body={}).execute()[
            'uploadUrl']
    logging.debug("Create Upload URL", upload_url)

    with TemporaryFile() as data:
        with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
            zipdir(orchestrator.__path__[0], archive)
        data.seek(0)
        headers = {
            'content-type': 'application/zip',
            'x-goog-content-length-range': '0,104857600'
        }
        logging.debug("Create Upload URL",
                      requests.put(upload_url, headers=headers, data=data))
    return upload_url


def create_cloud_function(project, region, function_name,
                          instance_zone, instance_name, topic):
    # create pubsub topic
    full_topic = create_topic(project, topic)

    parent = 'projects/{}/locations/{}'.format(project, region)
    upload_url = create_upload_url(parent)
    config = {
        "name": parent + '/functions/' + function_name,
        "entryPoint": "launch",
        "runtime": "python37",
        "availableMemoryMb": 128,
        # "serviceAccountEmail": string,
        # "updateTime": string,
        # "versionId": string,
        "environmentVariables": {
            "BUDGET_PROJECT": project,
            "BUDGET_ZONE": instance_zone,
            "BUDGET_INSTANCE": instance_name
        },
        # "vpcConnectorEgressSettings": "ALL_TRAFFIC",
        # "ingressSettings": "ALLOW_INTERNAL_ONLY",
        # "sourceArchiveUrl": "",
        "sourceUploadUrl": upload_url,
        "eventTrigger": {
            "eventType": "providers/cloud.pubsub/eventTypes/topic.publish",
            "resource": f"{full_topic}"
        }
    }

    logging.debug(f'Creating function with config: {config}')
    res = cloud_functions_api.create(
        location=parent,
        body=config).execute()
    logging.debug(f'Function {function_name} created. Response: {res}')
    return res
