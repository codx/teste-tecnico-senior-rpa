import json
import logging
import pika
from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQManager:
    _instance = None
    _connection = None
    _channel = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RabbitMQManager, cls).__new__(cls)
        return cls._instance

    def _connect(self):
        if not self._connection or self._connection.is_closed:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()

            self._channel.queue_declare(queue="jobs_queue_dlq", durable=True)

            args = {
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": "jobs_queue_dlq",
            }
            self._channel.queue_declare(
                queue="jobs_queue", durable=True, arguments=args
            )

        return self._channel

    def publish(self, job_id, job_type):
        try:
            channel = self._connect()
            message = {"job_id": job_id, "type": job_type}
            channel.basic_publish(
                exchange="",
                routing_key="jobs_queue",
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            logger.info(f"Published job {job_id} ({job_type}) to RabbitMQ")
        except Exception as e:
            logger.error(f"Erro ao publicar no RabbitMQ: {e}")
            # Reset connection on error to force reconnect next time
            if self._connection and not self._connection.is_closed:
                try:
                    self._connection.close()
                except Exception:
                    pass
            self._connection = None
            raise


rabbitmq_manager = RabbitMQManager()


def publish_job(job_id, job_type):
    rabbitmq_manager.publish(job_id, job_type)


def get_rabbitmq_connection():
    """Helper for worker or other legacy code needing direct connection."""
    params = pika.URLParameters(settings.RABBITMQ_URL)
    return pika.BlockingConnection(params)
