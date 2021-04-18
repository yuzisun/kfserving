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

from typing import List, Dict
from . import KFModel
from .kfmodel import PREDICTOR_V2_URL_FORMAT, PREDICTOR_URL_FORMAT
import json
import tornado.web


class PipelineModels(KFModel):
    def __init__(self, name: str, models: List[KFModel]):
        super().__init__(name)
        self.models = models

    async def predict(self, data: Dict) -> Dict:
        """
        PipelineModels chain the calls of all the models, the output of a model is used as the input of the next model
        :param data:
        :return:
        """
        request = data
        for model in self.models:
            predict_url = PREDICTOR_URL_FORMAT.format(model.predictor_host, model.name)
            if model.protocol == "v2":
                predict_url = PREDICTOR_V2_URL_FORMAT.format(model.predictor_host, model.name)
            response = await model._http_client.fetch(
                predict_url,
                method='POST',
                request_timeout=model.timeout,
                body=json.dumps(request)
            )
            if response.code != 200:
                raise tornado.web.HTTPError(
                    status_code=response.code,
                    reason=response.body)
            request = json.loads(response.body)
        return request




