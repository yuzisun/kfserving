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

import unittest.mock as mock
import kfserving
import time
import asyncio


async def test_batcher_default():
    batch_queue = kfserving.BatchQueue()
    batch_queue.put({"instances": [1, 2, 3]})
    batch_queue.put({"instances": [1, 2, 3]})
    results = await batch_queue.wait_for_batch()
    assert len(results) == 1


async def test_batcher_default_wait_first():
    batch_queue = kfserving.BatchQueue()
    tasks = [asyncio.create_task(batch_queue.wait_for_batch())]
    batch_queue.put({"instances": [1, 2, 3]})
    batch_queue.put({"instances": [1, 2, 3]})
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert len(results[0]) == 1


async def test_batcher_max_time():
    batch_queue = kfserving.BatchQueue(10, 1)
    batch_queue.put({"instances": [1, 2, 3]})
    batch_queue.put({"instances": [1, 2, 3]})
    results = await batch_queue.wait_for_batch()
    assert len(results) == 2


async def test_batcher_max_batch_size():
    batch_queue = kfserving.BatchQueue(10, 1)
    for i in range(1, 11):
        batch_queue.put({"instances": [1, 2, 3]})
        time.sleep(0.01)
    results = await batch_queue.wait_for_batch()
    assert len(results) == 10
