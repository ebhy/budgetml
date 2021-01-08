import base64
import inspect
import logging
import os
import pathlib
from typing import Text, Any
from uuid import uuid4

import docker
import googleapiclient.discovery

from budgetml.constants import BUDGETML_BASE_IMAGE_NAME
from budgetml.gcp.addresses import create_static_ip, release_static_ip
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
        self.region = region

        if static_ip is None:
            self.static_ip = None
        else:
            self.static_ip = static_ip

        # Initialize compute REST API client
        self.compute = googleapiclient.discovery.build('compute', 'v1')

    def create_static_ip(self, static_ip_name: Text):
        res = create_static_ip(
            self.compute,
            project=self.project,
            region=self.region,
            static_ip_name=static_ip_name,
        )
        self.static_ip = res['address']
        return self.static_ip

    def release_static_ip(self, static_ip: Text):
        return release_static_ip(
            self.compute,
            project=self.project,
            region=self.region,
            static_ip=static_ip,
        )

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

    def get_docker_compose_contents(self, docker_compose_path: Text = None):
        if docker_compose_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
            docker_compose_path = os.path.join(
                base_path, 'template-compose.yaml')

        with open(docker_compose_path, 'r') as f:
            docker_compose_content = f.read()
            return docker_compose_content

    def get_nginx_conf_contents(self,
                                domain: Text,
                                subdomain: Text,
                                nginx_config_path: Text = None):
        if nginx_config_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
            nginx_config_path = os.path.join(
                base_path, 'template-nginx.conf')

        with open(nginx_config_path, 'r') as f:
            nginx_config_content = f.read()
            nginx_config_content = nginx_config_content.replace(
                "$BUDGET_DOMAIN", f'{subdomain}.{domain}')
            return nginx_config_content

    def create_start_up(self,
                        predictor_class: Any,
                        bucket: Text,
                        domain: Text,
                        subdomain: Text,
                        username: Text,
                        password: Text):
        file_name = inspect.getfile(predictor_class)
        entrypoint = predictor_class.__name__

        # upload predictor to gcs
        predictor_gcs_path = f'predictors/{self.unique_id}/{entrypoint}.py'
        upload_blob(bucket, file_name, predictor_gcs_path)

        context_dir = '/home/budgetml'
        template_dockerfile_location = f'{context_dir}/template.Dockerfile'
        requirements_location = f'{context_dir}/custom_requirements.txt'
        template_dockercompose_location = f'{context_dir}/docker-compose.yaml'
        nginx_conf_location = f'{context_dir}/nginx.conf'
        certs_path = f'{context_dir}/certs/'

        # create script
        script = '#!/bin/bash' + '\n'

        # become superuser
        script += f'sudo -s' + '\n'

        # create context
        script += f'mkdir {context_dir}' + '\n'

        # go into tmp directory
        script += f'cd {context_dir}' + '\n'

        # get metadata
        script += 'export DOCKER_TEMPLATE=$(curl ' \
                  'http://metadata.google.internal/computeMetadata/v1' \
                  '/instance/attributes/DOCKER_TEMPLATE -H "Metadata-Flavor: ' \
                  '' \
                  '' \
                  '' \
                  'Google")' + '\n'
        script += 'export REQUIREMENTS=$(curl ' \
                  'http://metadata.google.internal/computeMetadata/v1' \
                  '/instance/attributes/REQUIREMENTS -H "Metadata-Flavor: ' \
                  'Google")' + '\n'
        script += 'export DOCKER_COMPOSE_TEMPLATE=$(curl ' \
                  'http://metadata.google.internal/computeMetadata/v1' \
                  '/instance/attributes/DOCKER_COMPOSE_TEMPLATE -H ' \
                  '"Metadata-Flavor: ' \
                  'Google")' + '\n'
        script += 'export NGINX_CONF_TEMPLATE=$(curl ' \
                  'http://metadata.google.internal/computeMetadata/v1' \
                  '/instance/attributes/NGINX_CONF_TEMPLATE -H ' \
                  '"Metadata-Flavor: ' \
                  'Google")' + '\n'

        # delete temporary files
        script += f'rm {template_dockerfile_location}' + '\n'
        script += f'rm {requirements_location}' + '\n'
        script += f'rm {template_dockercompose_location}' + '\n'
        script += f'rm {nginx_conf_location}' + '\n'

        # write temporary files
        script += f'echo $DOCKER_TEMPLATE | base64 --decode >> ' \
                  f'{template_dockerfile_location}' + '\n'
        script += f'echo $REQUIREMENTS | base64 --' \
                  f'decode >> {requirements_location}' + '\n'
        script += f'echo $DOCKER_COMPOSE_TEMPLATE | base64 --decode >> ' \
                  f'{template_dockercompose_location}' + '\n'
        script += f'echo $NGINX_CONF_TEMPLATE | base64 --' \
                  f'decode >> {nginx_conf_location}' + '\n'

        # export env variables
        script += f'export BUDGET_PREDICTOR_PATH=gs://{bucket}/' \
                  f'{predictor_gcs_path}' + '\n'
        script += f'export BUDGET_PREDICTOR_ENTRYPOINT={entrypoint}' + '\n'
        script += f'export BUDGET_DOMAIN={domain}' + '\n'
        script += f'export BUDGET_USERNAME={username}' + '\n'
        script += f'export BUDGET_PWD={password}' + '\n'
        script += f'export BUDGET_SUBDOMAIN={subdomain}' + '\n'
        script += f'export BUDGET_NGINX_PATH={nginx_conf_location}' + '\n'
        script += f'export BUDGET_CERTS_PATH={certs_path}' + '\n'
        script += f'export BASE_IMAGE={BUDGETML_BASE_IMAGE_NAME}' + '\n'

        # This generates a unique token for this instance and passes to
        # gunicorn to be picked up later in app:main
        script += f'export BUDGET_TOKEN={str(uuid4())}' + '\n'

        # download gcloud
        script += f'docker pull google/cloud-sdk:321.0.0' + '\n'

        # run docker-compose
        script += \
            'docker run ' \
            f'-e BUDGET_PREDICTOR_PATH=$BUDGET_PREDICTOR_PATH ' \
            f'-e BUDGET_PREDICTOR_ENTRYPOINT=$BUDGET_PREDICTOR_ENTRYPOINT ' \
            f'-e BUDGET_USERNAME=$BUDGET_USERNAME ' \
            f'-e BUDGET_PWD=$BUDGET_PWD ' \
            f'-e BUDGET_DOMAIN=$BUDGET_DOMAIN ' \
            f'-e BUDGET_SUBDOMAIN=$BUDGET_SUBDOMAIN ' \
            f'-e BUDGET_NGINX_PATH=$BUDGET_NGINX_PATH ' \
            f'-e BUDGET_CERTS_PATH=$BUDGET_CERTS_PATH ' \
            f'-e BASE_IMAGE=$BASE_IMAGE ' \
            f'-e BUDGET_TOKEN=$BUDGET_TOKEN ' \
            '--rm -v /var/run/docker.sock:/var/run/docker.sock -v ' \
            '"$PWD:$PWD" -w="$PWD" docker/compose:1.24.0 up -d'

        logging.debug(f'Startup script: {script}')
        return script

    def create_shut_down(self, bucket_name):
        shutdown_script = '#!/bin/bash' + '\n'
        shutdown_script += 'echo $(date) >> trigger.txt' + '\n'
        shutdown_script += \
            f'docker run -v "$PWD:$PWD" -w "$PWD" google/cloud-sdk gsutil ' \
            f'cp trigger.txt gs://{bucket_name}/trigger.txt' + '\n'
        logging.debug(f'Shutdown script: {shutdown_script}')
        return shutdown_script

    def create_cloud_function(self, instance_name, bucket_name):
        function_name = 'function-' + instance_name
        create_gcp_function(self.project, self.region, function_name,
                            self.zone, instance_name, bucket_name)
        return function_name

    def launch(self,
               predictor_class,
               domain: Text,
               subdomain: Text = 'budget',
               username: Text = 'budget',
               password: Text = str(uuid4()),
               requirements_path: Text = None,
               dockerfile_path: Text = None,
               bucket_name: Text = None,
               instance_name: Text = None,
               machine_type: Text = 'e2-medium',
               preemptible: bool = True,
               static_ip: Text = None):
        """
        Launches the VM.

        :param predictor_class: Class of type budgetml.BasePredictor.
        :param domain:
        :param subdomain:
        :param username:
        :param password:
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

        static_ip_name = f'ip-{instance_name}'

        if static_ip is None:
            self.create_static_ip(static_ip_name)
        else:
            self.static_ip = static_ip

        # Create bucket if it doesnt exist
        create_bucket_if_not_exists(bucket_name)

        cloud_function_name = \
            self.create_cloud_function(instance_name, bucket_name)

        startup_script = self.create_start_up(
            predictor_class,
            bucket_name,
            domain,
            subdomain,
            username,
            password)

        shutdown_script = self.create_shut_down(bucket_name)

        # create docker template content
        docker_template_content = self.get_docker_file_contents(
            dockerfile_path)

        # create requirements content
        requirements_content = self.get_requirements_file_contents(
            requirements_path)

        docker_compose_content = self.get_docker_compose_contents()
        nginx_conf_content = self.get_nginx_conf_contents(domain, subdomain)

        # encode the files to preserve the structure like newlines
        requirements_content = base64.b64encode(
            requirements_content.encode()).decode()
        docker_template_content = base64.b64encode(
            docker_template_content.encode()).decode()
        docker_compose_content = base64.b64encode(
            docker_compose_content.encode()).decode()
        nginx_conf_content = base64.b64encode(
            nginx_conf_content.encode()).decode()

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
            docker_compose_content,
            nginx_conf_content,
        )
        logging.info(f'Username: {username}. Password: {password}')
        return username, password

    def launch_local(self,
                     predictor_class,
                     requirements_path: Text = None,
                     dockerfile_path: Text = None,
                     bucket_name: Text = None,
                     username: Text = 'budget',
                     password: Text = str(uuid4())):

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

        logging.debug('Building docker image..')

        generator = client.images.build(
            path=tmp_dir,
            dockerfile='template.Dockerfile',
            tag=tag,
        )

        # # stream logs
        # while True:
        #     try:
        #         output = generator.__next__
        #         output = output.strip('\r\n')
        #         json_output = json.loads(output)
        #         if 'stream' in json_output:
        #             logging.debug(json_output['stream'].strip('\n'))
        #     except StopIteration:
        #         logging.debug("Docker image build complete.")
        #         break
        #     except ValueError:
        #         logging.debug(f"Error parsing output from docker image "
        #                       f"build: {output}")

        file_name = inspect.getfile(predictor_class)
        entrypoint = predictor_class.__name__

        # upload predictor to gcs
        predictor_gcs_path = f'predictors/{self.unique_id}/{entrypoint}.py'
        upload_blob(bucket_name, file_name, predictor_gcs_path)

        BUDGET_PREDICTOR_PATH = f'gs://{bucket_name}/{predictor_gcs_path}'
        BUDGET_PREDICTOR_ENTRYPOINT = predictor_class.__name__

        credentials_path = '/app/sa.json'
        ports = {'80/tcp': 8000}

        token = str(uuid4())

        environment = [
            f"BUDGET_PREDICTOR_PATH={BUDGET_PREDICTOR_PATH}",
            f'BUDGET_PREDICTOR_ENTRYPOINT={BUDGET_PREDICTOR_ENTRYPOINT}',
            f'BUDGET_USERNAME={username}',
            f'BUDGET_PWD={password}',
            f'GOOGLE_APPLICATION_CREDENTIALS={credentials_path}',
            f'BUDGET_TOKEN={token}'
        ]

        volumes = {os.environ['GOOGLE_APPLICATION_CREDENTIALS']: {
            'bind': f'{credentials_path}', 'mode': 'ro'}}
        logging.debug(
            f'Running docker container {tag} with env: {environment}, '
            f'ports: {ports}, volumes: {volumes}')

        docker_cmd = \
            f"docker run -it -e BUDGET_PREDICTOR_PATH=" \
            f"{BUDGET_PREDICTOR_PATH} -e " \
            f"BUDGET_PREDICTOR_ENTRYPOINT=" \
            f"{BUDGET_PREDICTOR_ENTRYPOINT} -e " \
            f'BUDGET_TOKEN="{token}" -e ' \
            f'BUDGET_USERNAME="{username}" -e ' \
            f'BUDGET_PWD="{password}" -e ' \
            f"GOOGLE_APPLICATION_CREDENTIALS=/app/sa.json -p " \
            f"8000:80 -v " \
            f"{os.environ['GOOGLE_APPLICATION_CREDENTIALS']}:/app/sa.json " \
            f"{tag}"
        logging.debug(f"To run it natively, you can use: \n{docker_cmd}")
        container = client.containers.run(
            tag,
            ports=ports,
            environment=environment,
            auto_remove=True,
            detach=True,
            name=tag,
            volumes=volumes
        )
        logging.debug(container.logs())
        logging.info(f'Username: {username}\t Password: {password}')
        return username, password
