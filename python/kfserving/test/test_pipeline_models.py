# Copyright 2020 kubeflow.org.
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
import pytest
from kfserving import kfmodel
from kfserving import kfserver
from kfserving.pipeline_models import PipelineModels
from kfserving.kfmodel_repository import KFModelRepository
from tornado.httpclient import HTTPClientError


class Model1(kfmodel.KFModel):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.ready = False

    def load(self):
        self.ready = True

    async def predict(self, request):
        return {"predictions": [[1, 2]]}


class Model2(kfmodel.KFModel):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.ready = False

    def load(self):
        self.ready = True

    async def predict(self, request):
        return {"predictions": [[3, 4]]}


class TestPipelineModel:

    @pytest.fixture(scope="class")
    def app(self):  # pylint: disable=no-self-use
        model1 = Model1("model1")
        model2 = Model2("model2")
        model = PipelineModels("pipeline", [model1, model2])
        model.load()
        server = kfserver.KFServer()
        server.register_model(model)
        server.register_model(model1)
        server.register_model(model2)
        return server.create_application()

    async def test_liveness(self, http_server_client):
        resp = await http_server_client.fetch('/')
        assert resp.code == 200

    async def test_model(self, http_server_client):
        resp = await http_server_client.fetch('/v1/models/pipeline')
        assert resp.code == 200

    async def test_predict(self, http_server_client):
        resp = await http_server_client.fetch('/v1/models/model1:predict',
                                              method="POST",
                                              body=b'{"instances":[[1,2]]}')
        assert resp.code == 200
        assert resp.body == b'{"predictions": [[1, 2]]}'
        assert resp.headers['content-type'] == "application/json; charset=UTF-8"
        resp = await http_server_client.fetch('/v1/models/model2:predict',
                                              method="POST",
                                              body=b'{"instances":[[1,2]]}')
        assert resp.code == 200
        assert resp.body == b'{"predictions": [[3, 4]]}'
        assert resp.headers['content-type'] == "application/json; charset=UTF-8"
