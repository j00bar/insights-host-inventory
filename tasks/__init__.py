import os
import json
from kafka import KafkaConsumer
from threading import Thread, Local
import logging

from app.models import Host, SystemProfileSchema

logger = logging.getLogger(__name__)
TOPIC = os.environ.get("KAFKA_TOPIC")
KAFKA_GROUP = os.environ.get("KAFKA_GROUP", "inventory")
BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
threadctx = Local()


def msg_handler(parsed):
    id_ = parsed["id"]
    threadctx.request_id = parsed["request_id"]
    host = Host.query.get(id_)
    if host is None:
        logger.error("Host with id [%s] not found!", id_)
        return
    profile = SystemProfileSchema(strict=True).load(parsed["system_profile"])
    host._update_system_profile(profile)
    host.save()


def start_consumer(handler, consumer=None):

    if consumer is None:
        consumer = KafkaConsumer(
            TOPIC,
            group_id=KAFKA_GROUP,
            bootstrap_servers=BOOTSTRAP_SERVERS)

    def _f():
        while True:
            for msg in consumer:
                handler(json.loads(msg.value))

    t = Thread(
        target=_f,
        daemon=True)
    t.start()
