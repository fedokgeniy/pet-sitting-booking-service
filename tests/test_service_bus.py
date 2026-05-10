from unittest.mock import patch, MagicMock

from app import service_bus


def test_publish_skipped_without_config():
    with patch.object(service_bus, "SEND_CONNECTION_STRING", None), \
         patch.object(service_bus, "QUEUE_NAME", None), \
         patch.object(service_bus, "ServiceBusClient") as client_cls:
        service_bus.publish_booking_event("BookingCompleted", {"booking_id": "b1"})
        client_cls.from_connection_string.assert_not_called()


def test_publish_sends_message_when_configured():
    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_sender = MagicMock()
    fake_sender.__enter__.return_value = fake_sender
    fake_client.get_queue_sender.return_value = fake_sender

    with patch.object(service_bus, "SEND_CONNECTION_STRING", "Endpoint=sb://x"), \
         patch.object(service_bus, "QUEUE_NAME", "q"), \
         patch.object(service_bus, "ServiceBusClient") as client_cls:
        client_cls.from_connection_string.return_value = fake_client
        service_bus.publish_booking_event("BookingCompleted", {"booking_id": "b1"})
        fake_sender.send_messages.assert_called_once()
