import logging

from google.cloud import scheduler


def create_scheduler_job(
        project_id,
        topic,
        schedule='* * * * *',
        location_id='us-central1'):
    """Create a job with a PubSub topic via the Cloud Scheduler API"""

    # Create a client.
    client = scheduler.CloudSchedulerClient()

    # Construct the fully qualified location path.
    parent = f"projects/{project_id}/locations/{location_id}"

    # Construct the request body.
    job = {
        'pubsub_target': {
            'topic_name': f'projects/{project_id}/topics/{topic}',
            'data': '{}'.encode("utf-8")
        },
        'schedule': schedule,
        'time_zone': 'America/Los_Angeles'
    }

    # Use the client to send the job creation request.
    response = client.create_job(
        request={
            "parent": parent,
            "job": job
        }
    )

    logging.debug('Created scheduler job: {}'.format(response.name))
    return response
