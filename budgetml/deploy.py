import logging
import subprocess
import time
from typing import Text

import googleapiclient.discovery

from budgetml.gcp.addresses import create_static_ip
from budgetml.gcp.compute import create_instance
from budgetml.gcp.function import create_cloud_function as create_gcp_function

logging.basicConfig(level=logging.DEBUG)


class BudgetML:
    def __init__(self,
                 project: Text,
                 zone: Text = 'us-central1-a',
                 region: Text = 'us-central1',
                 static_ip: Text = None):
        self.project = project
        self.zone = zone

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

    def create_start_up(self):
        return ''

    def create_shut_down(self, cloud_function_name):
        # THIS WILL ONLY WORK IF GCLOUD CLI IS AUTHENTICATED TO THE RIGHT
        # PROJECT
        token = subprocess.check_output(
            "gcloud auth print-identity-token", shell=True)
        token = token.decode().strip('\n')
        trigger_url = f'https://{self.region}-' \
                      f'{self.project}.cloud' \
                      f'functions.net/{cloud_function_name}'
        shutdown_script = f'curl -X POST {trigger_url} ' \
                          f'-H "Authorization: bearer {token}" ' \
                          '-H "Content-Type:application/json" --data "{}"'
        logging.debug(f'Shutdown script: {shutdown_script}')
        return shutdown_script

    def create_cloud_function(self, instance_name):
        function_name = 'function-' + instance_name
        create_gcp_function(self.project, self.region, function_name,
                            self.zone, instance_name)
        return function_name

    def launch(self,
               instance_name: Text = f'budget-{int(time.time())}',
               machine_type: Text = 'e2-medium',
               preemptible: bool = True,
               static_ip_name: Text = None):
        """
        Launches the VM.

        :param instance_name:
        :param machine_type:
        :param preemptible:
        :return:
        """
        if static_ip_name is None:
            static_ip_name = f'ip-{instance_name}'

        self.create_static_ip_if_not_exists(static_ip_name)

        cloud_function_name = self.create_cloud_function(instance_name)

        startup_script = self.create_start_up()
        shutdown_script = self.create_shut_down(cloud_function_name)

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
            preemptible
        )


#### #####

budgetml = BudgetML(
    project='budgetml'
)

budgetml.launch()
