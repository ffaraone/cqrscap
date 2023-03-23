import logging
import secrets

import ujson

from kombu import (
    Connection,
    Exchange,
    Queue,
)
from kombu.mixins import ConsumerMixin


logger = logging.getLogger(__name__)


class _KombuConsumer(ConsumerMixin):

    def __init__(self, url, exchange_name, callback, cqrs_ids=None):
        self.connection = Connection(url)
        self.exchange = Exchange(
            exchange_name,
            type='topic',
            durable=True,
        )
        self.queue_name = f'cqrs-monit-{secrets.token_hex(8)}'
        self.callback = callback
        self.queues = []
        self.cqrs_ids = cqrs_ids

        self._init_queues()

    def _init_queues(self):
        channel = self.connection.channel()
        for cqrs_id in self.cqrs_ids:
            q = Queue(
                self.queue_name,
                exchange=self.exchange,
                routing_key=cqrs_id,
                auto_delete=True
            )
            q.maybe_bind(channel)
            q.declare()
            self.queues.append(q)


    def get_consumers(self, Consumer, channel):
        return [
            Consumer(
                queues=self.queues,
                callbacks=[self.callback],
                prefetch_count=1,
                auto_declare=True,
            ),
        ]


class CQRSConsumer:
    def __init__(
            self, cqrs_ids, hostname, port,
            username, password, exchange_name, callback,
        ):
        self.cqrs_ids = cqrs_ids
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.exchange_name = exchange_name
        self.callback = callback
        self.consumer = None


    def get_url(self):
        return f'amqp://{self.username}:{self.password}@{self.hostname}:{self.port}'


    def run(self):
        self.consumer = _KombuConsumer(
            self.get_url(),
            self.exchange_name,
            self.on_message,
            cqrs_ids=self.cqrs_ids,
        )
        self.consumer.run()

    def stop(self):
        if self.consumer:
            self.consumer.should_stop = True

    def on_message(self, body, message):
        try:
            dct = ujson.loads(body)
        except ValueError:
            logger.error("CQRS couldn't be parsed: {0}.".format(body))
            message.reject()
            return

        required_keys = {'instance_pk', 'signal_type', 'cqrs_id', 'instance_data'}
        for key in required_keys:
            if key not in dct:
                msg = "CQRS couldn't proceed, %s isn't found in body: %s."
                logger.error(msg, key, body)
                message.reject()
                return

        self.callback(dct)
        message.ack()
