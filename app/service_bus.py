import json
import os
from datetime import datetime

from azure.servicebus import ServiceBusClient, ServiceBusMessage

from .logging_config import get_logger

logger = get_logger(__name__)

QUEUE_NAME = os.getenv("SERVICE_BUS_QUEUE_NAME")
SEND_CONNECTION_STRING = os.getenv("SERVICE_BUS_SEND_CONNECTION_STRING")


def publish_booking_event(event_type: str, payload: dict) -> None:
    if not SEND_CONNECTION_STRING or not QUEUE_NAME:
        logger.warning("Service Bus send config missing, skip publish event=%s", event_type)
        return

    message_body = {
        "event_type": event_type,
        "published_at": datetime.utcnow().isoformat(),
        "payload": payload,
    }

    logger.info("Publishing event %s to queue %s", event_type, QUEUE_NAME)
    try:
        with ServiceBusClient.from_connection_string(SEND_CONNECTION_STRING) as client:
            with client.get_queue_sender(queue_name=QUEUE_NAME) as sender:
                sender.send_messages(ServiceBusMessage(json.dumps(message_body)))
        logger.info("Event %s published successfully", event_type)
    except Exception as ex:
        logger.exception("Failed to publish event %s: %s", event_type, ex)
        raise
