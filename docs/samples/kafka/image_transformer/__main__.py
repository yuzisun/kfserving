# Copyright 2019 kubeflow.org.
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

import kfserving
import argparse
import asyncio
from .image_transformer import ImageTransformer
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('message')

DEFAULT_MODEL_NAME = "model"

parser = argparse.ArgumentParser(parents=[kfserving.kfserver.parser])
parser.add_argument('--model_name', default=DEFAULT_MODEL_NAME,
                    help='The name that the model is served under.')
parser.add_argument('--predictor_host', help='The URL for the model predict function', required=True)
parser.add_argument('--topics', help='Kafka topic list', required=True)
parser.add_argument('--bootstrap_servers', help='Kafka bootstrap servers', required=True)
parser.add_argument('--consumer_group', help='Kafka consumer group id', required=True)

args, _ = parser.parse_known_args()


async def main():
    transformer = ImageTransformer(args.model_name, predictor_host=args.predictor_host)
    consumer = kfserving.KafkaConsumer(transformer, [args.topics], config={'bootstrap.servers':args.bootstrap_servers, 'group.id': args.consumer_group, 'auto.offset.reset': 'latest'})
    tasks = []
    tasks.append(asyncio.create_task(consumer.handle_batch()))
    consumer.consume_records()

asyncio.run(main())    
