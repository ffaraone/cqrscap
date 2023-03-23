import logging

from devtools import pformat

from cqrscap.consumer import CQRSConsumer


logger = logging.getLogger(__name__)


class Logger:
    def __init__(self, cqrs_ids, hostname, port, username, password, exchange_name):
        self.consumer = CQRSConsumer(
            cqrs_ids,
            hostname,
            port,
            username,
            password,
            exchange_name,
            self.on_cqrs_message,
        )

    def run(self):
        self.consumer.run()


    def on_cqrs_message(self, message):
        logger.info(pformat(message), extra={
            'cqrs_id': message['cqrs_id'],
            'cqrs_signal': message['signal_type'],
            'cqrs_instance_pk': message['instance_pk'],
        })