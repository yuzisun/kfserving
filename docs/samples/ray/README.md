# Predict on an InferenceService using Ray 

This guide demonstrates how to serve ML models using `Ray Serve` library and deploy onto KFServing. 

[Ray Serve](https://docs.ray.io/en/master/serve) is a scalable model-serving library built with Ray.
`Ray Serve` utilizes Ray actors controller, router and worker replica to make up the server instances.
An HTTP request is received and the endpoint is associated with the HTTP url path, one or more backends 
are selected to handle the requests and requests are placed onto the queue for an available worker to process.

## Setup

Before starting this guide, make sure you have the following:

* Your ~/.kube/config should point to a cluster with [KFServing installed](https://github.com/kubeflow/kfserving/#install-kfserving).
* Your cluster's Istio Ingress gateway must be [network accessible](https://istio.io/latest/docs/tasks/traffic-management/ingress/ingress-control/).
* Docker and Docker hub must be properly configured on your local system
* Python 3.6 or above
  * Install required packages `ray[server]` and `scikit-learn` on your local system:

    ```shell
    pip install ray[serve]
    ```

## Deploy a Multi Model InferenceService with Ray Serve

### Build a Multi Model Server using Ray Serve

The following code defines a Multi Model Server with a Iris XgBoost model and a ResNet Pytorch model.
`Ray Serve` spawns two workers each loads a model and uses the `HTTPProxyActor` to route the requests so that
inference requests for the two models can be processed in parallel.

```python
from ray import serve
import time
from .image_model import ImageModel
from .xgboost import BoostingModel
# This model server is composed of two models
# - Iris XgBoost Model
# - ResNet Pytorch Model

# Let's define two models and expose the model endpoints


client = serve.start(detached=True, http_host='0.0.0.0', http_port=8080)
client.create_backend("resnet18", ImageModel)
client.create_backend("iris", BoostingModel)
client.create_endpoint("pytorch_predictor", backend="resnet18", route="/v2/models/resnet18", methods=["POST"])
client.create_endpoint("xgboost_predictor", backend="iris", route="/v2/models/iris", methods=["POST"])


try:
   while True:
      time.sleep(10)
      continue
except KeyboardInterrupt:
   print("Shutdown...")
   serve.shutdown()
   ray.shutdown()
```

### Deploy InferenceService

```shell

# Replace {docker_username} with your Docker Hub username
docker build -t {docker_username}/multimodel:latest . --rm
docker push {docker_username}/multimodel:latest
```

The following is an example YAML file for specifying the resources required to run an
InferenceService in KFServing. Replace `{docker_username}` with your Docker Hub username
and save it to `bentoml.yaml` file:

```yaml
apiVersion: serving.kubeflow.org/v1alpha2
kind: InferenceService
metadata:
  name: multimodel
spec:
  default:
    predictor:
      custom:
        container:
          image: {docker_username}/multimodel:latest
```

Use `kubectl apply` command to deploy the InferenceService:

```shell
kubectl apply -f multimodel.yaml
```

### Run prediction
The first step is to [determine the ingress IP and ports](../../../README.md#determine-the-ingress-ip-and-ports) and set `INGRESS_HOST` and `INGRESS_PORT`

```shell
MODEL_NAME=iris-classifier
SERVICE_HOSTNAME=$(kubectl get inferenceservice ${MODEL_NAME} -o jsonpath='{.status.url}' | cut -d "/" -f 3)

curl -v -H "Host: ${SERVICE_HOSTNAME}" \
  --header "Content-Type: application/json" \
  --request POST \
  --data '[[5.1, 3.5, 1.4, 0.2]]' \
  http://${INGRESS_HOST}:${INGRESS_PORT}/v2/models/iris

curl -v -H "Host: ${SERVICE_HOSTNAME}" \
  --header "Content-Type: application/json" \
  --request POST \
  --data image.png \
  http://${INGRESS_HOST}:${INGRESS_PORT}/v2/models/resnet18
```

### Delete deployment

```shell
kubectl delete -f multimodel.yaml
```


## Deploy a Model Pipeline InferenceService with Ray Serve

### Build a Model Pipeline using Ray Serve

The following code defines a Model pipeline which is composed of two models and invoked in sequence.

```python
from random import random
import requests
from ray import serve
import time

# Our pipeline will be structured as follows:
# - Input comes in, the composed model sends it to model_one
# - model_one outputs a random number between 0 and 1, if the value is
#   greater than 0.5, then the data is sent to model_two
# - otherwise, the data is returned to the user.

# Let's define two models that just print out the data they received.


def model_one(request):
    print("Model 1 called with data ", request.args.get("data"))
    return random()


def model_two(request):
    print("Model 2 called with data ", request.args.get("data"))
    return request.args.get("data")


class ComposedModel:
    def __init__(self):
        client = serve.connect()
        self.model_one = client.get_handle("model_one")
        self.model_two = client.get_handle("model_two")

    # This method can be called concurrently!
    async def __call__(self, flask_request):
        data = flask_request.data

        score = await self.model_one.remote(data=data)
        if score > 0.5:
            result = await self.model_two.remote(data=data)
            result = {"model_used": 2, "score": score}
        else:
            result = {"model_used": 1, "score": score}

        return result

client = serve.start(detached=True, http_host='0.0.0.0', http_port=8080)
client.create_backend("model_one", model_one)
client.create_endpoint("model_one", backend="model_one")

client.create_backend("model_two", model_two)
client.create_endpoint("model_two", backend="model_two")

# max_concurrent_queries is optional. By default, if you pass in an async
# function, Ray Serve sets the limit to a high number.
client.create_backend(
    "composed_backend", ComposedModel, config={"max_concurrent_queries": 10})
client.create_endpoint(
    "composed", backend="composed_backend", route="/v2/models/composed")
try:
   while True:
      time.sleep(10)
      continue
except KeyboardInterrupt:
   print("Shutdown...")
   serve.shutdown()
   ray.shutdown()

```

### Deploy InferenceService

```shell

# Replace {docker_username} with your Docker Hub username
docker build -t {docker_username}/pipline:latest . --rm
docker push {docker_username}/pipline:latest
```

The following is an example YAML file for specifying the resources required to run an
InferenceService in KFServing. Replace `{docker_username}` with your Docker Hub username
and save it to `pipline.yaml` file:

```yaml
apiVersion: serving.kubeflow.org/v1alpha2
kind: InferenceService
metadata:
  name: multimodel
spec:
  default:
    predictor:
      custom:
        parallelism: 10
        container:
          image: {docker_username}/pipline:latest
```

Use `kubectl apply` command to deploy the InferenceService:

```shell
kubectl apply -f pipline.yaml
```

### Run prediction
The first step is to [determine the ingress IP and ports](../../../README.md#determine-the-ingress-ip-and-ports) and set `INGRESS_HOST` and `INGRESS_PORT`

```shell
MODEL_NAME=iris-classifier
SERVICE_HOSTNAME=$(kubectl get inferenceservice ${MODEL_NAME} -o jsonpath='{.status.url}' | cut -d "/" -f 3)

curl -v -H "Host: ${SERVICE_HOSTNAME}" \
  --header "Content-Type: application/json" \
  --request POST \
  --data 'hey' \
  http://${INGRESS_HOST}:${INGRESS_PORT}/v2/models/composed
```

### Delete deployment

```shell
kubectl delete -f pipeline.yaml
```

