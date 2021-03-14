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
from kfserving import Batcher
import json
import logging
import inspect


# KafkaConsumer is intended to be used along with KFModel.
class KafkaConsumer:

    def __init__(self, model: KFModel, topics: List, config: Dict):
        self.model = model
        self.consumer = Consumer(config)
        self.ready = False
        self.model.load()
        self.consumer.subscribe(topics)
        self.batcher = Batcher()

    def consume_records(self):
        try:
            while True:
                record = self.consumer.poll()
                if record:
                    if record.error():
                        logging.error(f'Consumer error: {record.error()}')
                    else:
                        logging.info(f'Received message: partition:{record.partition()}, offset:{record.offset()}')
                        data = record.value().decode('utf-8')
                        event = json.loads(data)

                        self.msg_process(event)
                        # commit offset
                else:
                    continue
        finally:
            self.consumer.close()

    def msg_process(self, event):
        request = self.model.preprocess(event)
        response = (await self.model.predict(request)) if inspect.iscoroutinefunction(self.model.predict) \
            else self.model.predict(request)
        self.model.postprocess(response)
