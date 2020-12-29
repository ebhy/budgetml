import base64
import inspect
import logging
import os
import pathlib
import subprocess
from typing import Text
from uuid import uuid4

import docker
import googleapiclient.discovery

from budgetml.constants import BUDGETML_BASE_IMAGE_NAME
from budgetml.gcp.addresses import create_static_ip
from budgetml.gcp.compute import create_instance
from budgetml.gcp.function import create_cloud_function as create_gcp_function
from budgetml.gcp.storage import upload_blob, create_bucket_if_not_exists

logging.basicConfig(level=logging.DEBUG)


class BudgetML:
    def __init__(self,
                 project: Text,
                 zone: Text = 'us-central1-a',
                 unique_id: Text = str(uuid4()),
                 region: Text = 'us-central1',
                 static_ip: Text = None):

        self.project = project
        self.zone = zone
        self.unique_id = unique_id

        if static_ip is None:
            self.static_ip = None
        else:
            self.static_ip = static_ip

        self.region = region

        # Initialize compute REST API client
        self.compute = googleapiclient.discovery.build('compute', 'v1')

    def create_static_ip_if_not_exists(self, static_ip_name: Text):
        if self.static_ip is None:
            res = create_static_ip(
                self.compute,
                project=self.project,
                region=self.region,
                static_ip_name=static_ip_name,
            )
            self.static_ip = res['address']

    def create_start_up(self, predictor_class, bucket):
        file_name = inspect.getfile(predictor_class)
        entrypoint = predictor_class.__name__

        # upload predictor to gcs
        predictor_gcs_path = f'predictors/{self.unique_id}/{entrypoint}.py'
        upload_blob(bucket, file_name, predictor_gcs_path)

        template_dockerfile_location = '/tmp/template.Dockerfile'
        requirements_location = '/tmp/custom_requirements.txt'
        image_name = 'budgetml:0.0.1'

        # create script
        script = '#!/bin/bash' + '\n'

        # get metadata
        script += 'export DOCKER_TEMPLATE=$(curl ' \
                  'http://metadata.google.internal/computeMetadata/v1' \
                  '/instance/attributes/DOCKER_TEMPLATE -H "Metadata-Flavor: ' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  '' \
                  'Google")' + '\n'
        script += 'export REQUIREMENTS=$(curl ' \
                  'http://metadata.google.internal/computeMetadata/v1' \
                  '/instance/attributes/REQUIREMENTS -H "Metadata-Flavor: ' \
                  'Google")' + '\n'

        # write temporary files
        script += f'echo $DOCKER_TEMPLATE | base64 --decode >> ' \
                  f'{template_dockerfile_location}' + '\n'
        script += f'echo $REQUIREMENTS | base64 --' \
                  f'decode >> {requirements_location}' + '\n'

        # export enn variables
        script += f'export BUDGET_PREDICTOR_PATH=gs://{bucket}/' \
                  f'{predictor_gcs_path}' + \
                  '\n'
        script += f'export BUDGET_PREDICTOR_ENTRYPOINT={entrypoint}' + '\n'

        # go into tmp directory
        script += 'cd /tmp' + '\n'

        # docker build
        script += f'docker build -f {template_dockerfile_location} -t ' \
                  f'{image_name} .' + '\n'

        # docker-run
        script += f'docker run -d -e ' \
                  f'BUDGET_PREDICTOR_PATH=$BUDGET_PREDICTOR_PATH -e ' \
                  f'BUDGET_PREDICTOR_ENTRYPOINT=$BUDGET_PREDICTOR_ENTRYPOINT' \
                  f' {image_name}' + '\n'
        logging.debug(f'Startup script: {script}')
        return script

    def create_shut_down(self, cloud_function_name):
        # THIS WILL ONLY WORK IF GCLOUD CLI IS AUTHENTICATED TO THE RIGHT
        # PROJECT
        token = subprocess.check_output(
            "gcloud auth print-identity-token", shell=True)
        token = token.decode().strip('\n')
        trigger_url = f'https://{self.region}-' \
                      f'{self.project}.cloud' \
                      f'functions.net/{cloud_function_name}'
        shutdown_script = '#!/bin/bash' + '\n'
        shutdown_script += f'curl -X POST {trigger_url} ' \
                           f'-H "Authorization: bearer {token}" ' \
                           '-H "Content-Type:application/json" --data "{}"'
        logging.debug(f'Shutdown script: {shutdown_script}')
        return shutdown_script

    def create_cloud_function(self, instance_name):
        function_name = 'function-' + instance_name
        create_gcp_function(self.project, self.region, function_name,
                            self.zone, instance_name)
        return function_name

    def get_docker_file_contents(self, dockerfile_path: Text):
        if dockerfile_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
            dockerfile_path = os.path.join(base_path, 'template.Dockerfile')

        with open(dockerfile_path, 'r') as f:
            docker_template_content = f.read()
            # TODO: Maybe use env variables for this
            docker_template_content = docker_template_content.replace(
                "$BASE_IMAGE", BUDGETML_BASE_IMAGE_NAME)
        return docker_template_content

    def get_requirements_file_contents(self, requirements_path: Text):
        if requirements_path is None:
            requirements_content = ''
        else:
            with open(requirements_path, 'r') as f:
                requirements_content = f.read()
        return requirements_content

    def launch(self,
               predictor_class,
               requirements_path: Text = None,
               dockerfile_path: Text = None,
               bucket_name: Text = None,
               instance_name: Text = None,
               machine_type: Text = 'e2-medium',
               preemptible: bool = True,
               static_ip_name: Text = None):
        """
        Launches the VM.

        :param predictor_class: Class of type budgetml.BasePredictor.
        :param dockerfile_path:
        :param requirements_path:
        :param bucket_name:
        :param instance_name:
        :param machine_type:
        :param preemptible:
        :return:
        """
        if bucket_name is None:
            bucket_name = f'budget_bucket_{self.unique_id}'
        if instance_name is None:
            instance_name = f'budget-instance-' \
                            f'{self.unique_id.replace("_", "-")}'
        if static_ip_name is None:
            static_ip_name = f'ip-{instance_name}'

        # Create bucket if it doesnt exist
        create_bucket_if_not_exists(bucket_name)

        self.create_static_ip_if_not_exists(static_ip_name)

        cloud_function_name = self.create_cloud_function(instance_name)

        startup_script = self.create_start_up(predictor_class, bucket_name)
        shutdown_script = self.create_shut_down(cloud_function_name)

        # create docker template content
        docker_template_content = self.get_docker_file_contents(
            dockerfile_path)

        # create requirements content
        requirements_content = self.get_requirements_file_contents(
            requirements_path)

        # encode the files to preserve the structure like newlines
        requirements_content = base64.b64encode(
            requirements_content.encode()).decode()
        docker_template_content = base64.b64encode(
            docker_template_content.encode()).decode()

        logging.info(
            f'Launching GCP Instance {instance_name} with IP: '
            f'{self.static_ip} in project: {self.project}, zone: '
            f'{self.zone}. The machine type is: {machine_type}')
        create_instance(
            self.compute,
            self.project,
            self.zone,
            self.static_ip,
            instance_name,
            machine_type,
            startup_script,
            shutdown_script,
            preemptible,
            requirements_content,
            docker_template_content,
        )

    def launch_local(self,
                     predictor_class,
                     requirements_path: Text = None,
                     dockerfile_path: Text = None,
                     bucket_name: Text = None):

        # Create bucket if it doesnt exist
        if bucket_name is None:
            bucket_name = f'budget_bucket_{self.unique_id}'
        create_bucket_if_not_exists(bucket_name)

        # create docker template content
        docker_template_content = self.get_docker_file_contents(
            dockerfile_path)

        # create requirements content
        requirements_content = self.get_requirements_file_contents(
            requirements_path)

        tmp_dir = 'tmp'
        try:
            os.makedirs(tmp_dir)
        except OSError as e:
            # already exists
            pass

        tmp_reqs_path = os.path.join(tmp_dir, 'custom_requirements.txt')
        reqs_path = pathlib.Path(tmp_reqs_path)
        reqs_path.write_text(requirements_content)

        tmp_dockerfile_path = os.path.join(tmp_dir, 'template.Dockerfile')
        docker_path = pathlib.Path(tmp_dockerfile_path)
        docker_path.write_text(docker_template_content)

        # build image
        client = docker.from_env()
        tag = 'budget_local'

        client.images.build(
            path=tmp_dir,
            dockerfile='template.Dockerfile',
            tag=tag,
        )

        file_name = inspect.getfile(predictor_class)
        entrypoint = predictor_class.__name__

        # upload predictor to gcs
        predictor_gcs_path = f'predictors/{self.unique_id}/{entrypoint}.py'
        upload_blob(bucket_name, file_name, predictor_gcs_path)

        BUDGET_PREDICTOR_PATH = f'gs://{bucket_name}/{predictor_gcs_path}'
        BUDGET_PREDICTOR_ENTRYPOINT = predictor_class.__name__

        credentials_path = '/app/sa.json'
        ports = {'80/tcp': 8080}

        environment = [f"BUDGET_PREDICTOR_PATH={BUDGET_PREDICTOR_PATH}",
                       f'BUDGET_PREDICTOR_ENTRYPOINT='
                       f'{BUDGET_PREDICTOR_ENTRYPOINT}',
                       f'GOOGLE_APPLICATION_CREDENTIALS={credentials_path}']

        volumes = {os.environ['GOOGLE_APPLICATION_CREDENTIALS']: {
            'bind': f'{credentials_path}', 'mode': 'ro'}}
        logging.debug(
            f'Running docker container {tag} with env: {environment}, '
            f'ports: {ports}, volumes: {volumes}')
        container = client.containers.run(
            tag,
            ports=ports,
            environment=environment,
            auto_remove=True,
            detach=True,
            name=tag,
            volumes=volumes
        )
        print(container.logs())
