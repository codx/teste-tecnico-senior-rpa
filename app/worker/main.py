import json
import logging
import time

from app.core.config import setup_logging
from app.core.rabbitmq import get_rabbitmq_connection
from app.db.database import SessionLocal
from app.services.job_service import JobService

setup_logging()
logger = logging.getLogger("worker")


def process_job(ch, method, properties, body):
    data = json.loads(body)
    job_id = data.get("job_id")
    job_type = data.get("type")

    db = SessionLocal()
    service = JobService(db)

    try:
        service.update_job_status(job_id, "running")

        if job_type in ["hockey", "all"]:
            service.run_hockey_scrape(job_id)

        if job_type in ["oscar", "all"]:
            service.run_oscar_scrape(job_id)

        service.update_job_status(job_id, "completed")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.exception(f"Error processing job {job_id}")
        service.update_job_status(job_id, "failed", error=str(e))
        # Requeue=False will move the message to DLQ if configured
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        db.close()


def main():
    while True:
        try:
            connection = get_rabbitmq_connection()
            channel = connection.channel()

            # Declare DLQ and Main Queue with DLQ arguments
            channel.queue_declare(queue="jobs_queue_dlq", durable=True)
            args = {
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": "jobs_queue_dlq",
            }
            channel.queue_declare(queue="jobs_queue", durable=True, arguments=args)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue="jobs_queue", on_message_callback=process_job)

            logger.info("Worker waiting for messages...")
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Worker connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()
