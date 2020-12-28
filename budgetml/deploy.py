import time
from typing import Text

import googleapiclient.discovery

from budgetml.gcp.addresses import create_static_ip_address
from budgetml.gcp.compute import create_instance


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

    def create_static_ip_if_not_exists(self):
        if self.static_ip is not None:
            self.static_ip = create_static_ip_address(
                self.compute,
                project=self.project,
                region=self.region,
                static_ip=self.static_ip,
            )

    def create_start_up(self):
        pass

    def create_shut_down(self):
        pass

    def create_cloud_function(self):
        pass

    def launch(self,
               instance_name: Text = f'budget_{int(time.time())}',
               machine_type: Text = 'e2-medium',
               preemptible: bool = True):
        """
        Launches the VM.

        :param instance_name:
        :param machine_type:
        :param preemptible:
        :return:
        """
        self.static_ip = self.create_static_ip_if_not_exists()

        cloud_function_name = self.create_cloud_function()

        startup_script = self.create_start_up()
        shutdown_script = self.create_shut_down()

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
    predictor_class='',
    requirements='',
    gcp_project='',
    gcp_region='',
    static_ip='',
)

budgetml.push()

"gcloud compute instances create $INSTANCE_NAME " \
"--address $STATIC_IP_ADDRESS --network-tier=STANDARD --zone=us-central1-a " \
"--machine-type=n1-highmem-2 --boot-disk-size=20GB " \
"--metadata=GIT_USERNAME=$GIT_USERNAME,GIT_PASSWORD=$GIT_PASSWORD " \
"--no-restart-on-failure " \
"--maintenance-policy=TERMINATE --preemptible --tags=insecure-allow-all," \
"http-server,https-server " \
"--image=cos-stable-78-12499-89-0 --image-project=cos-cloud " \
"--metadata-from-file shutdown-script=.ci/shutdown-script.sh," \
"startup-script=.ci/startup-script.sh --scopes cloud-platform"
