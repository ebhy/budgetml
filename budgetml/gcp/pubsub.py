import logging

from google.cloud import pubsub_v1


def create_topic(project, topic):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic)
    topic = publisher.create_topic(request={"name": topic_path})
    logging.debug("Created topic: {}".format(topic.name))
    return topic.name
