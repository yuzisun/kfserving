# Copyright 2021 kubeflow.org.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict, List
from confluent_kafka import Consumer
from kfserving import KFModel
from kfserving import BatchQueue
import asyncio
import logging
import inspect


# KafkaConsumer is intended to be used along with KFModel.
class KafkaConsumer:

    def __init__(self, model: KFModel, topics: List, config: Dict):
        self.model = model
        self.consumer = Consumer(config)
        self.ready = False
        self.model.load()
        logging.info(f"subscribing to topics {topics}")
        self.consumer.subscribe(topics)
        logging.info(f"creating batch queue")
        self.batch_queue = BatchQueue()

    def consume_records(self):
        logging.info(f"start consuming records")
        try:
            while True:
                record = self.consumer.poll()
                if record:
                    if record.error():
                        logging.error(f'Consumer error: {record.error()}')
                    else:
                        logging.info(f'Received message: partition:{record.partition()}, offset:{record.offset()}')
                        logging.info(f'current qsiz {self.batch_queue.qsize()}')
                        self.batch_queue.put(record.value())
                else:
                    logging.info("no message")
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

    async def handle_batch(self):
        logging.info(f"start processing records")
        while True:
            logging.info(f'waiting for batch')
            batch = await self.batch_queue.wait_for_batch()
            logging.info(f'Received batch:{batch}')
            request = self.model.preprocess({"instances": batch})
            response = (await self.model.predict(request)) if inspect.iscoroutinefunction(self.model.predict) \
                else self.model.predict(request)
            logging.info(response)
            self.model.postprocess(response)
            # commit offset
            self.consumer.commit(asynchronous=False)

