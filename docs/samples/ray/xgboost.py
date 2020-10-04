from ray import serve
import pickle
import requests
from sklearn.datasets import load_iris
from sklearn.ensemble import GradientBoostingClassifier

# Train model
iris_dataset = load_iris()
model = GradientBoostingClassifier()
model.fit(iris_dataset["data"], iris_dataset["target"])

# Define Ray Serve model,
class BoostingModel:
    def __init__(self):
        self.model = model
        self.label_list = iris_dataset["target_names"].tolist()

    def __call__(self, flask_request):
        payload = flask_request.json["vector"]
        print("Worker: received flask request with data", payload)

        prediction = self.model.predict([payload])[0]
        human_name = self.label_list[prediction]
        return {"result": human_name}
