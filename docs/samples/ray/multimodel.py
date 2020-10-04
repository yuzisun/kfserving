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
