import io
from typing import Callable

import requests
import smart_open
from chalice import Chalice, Rate

from chitra.serve.cloud.base import CloudServer

S3 = "s3"
GCS = "gcs"

RATE_UNIT = {"m": Rate.MINUTES, "h": Rate.HOURS, "d": Rate.DAYS}


def infer_location_type(path: str):
    if path.startswith("s3"):
        return S3
    if path.startswith("gcs"):
        return GCS
    raise ValueError(f"Location type is not supported yet for path={path}")


def download_model(path: str, **kwargs) -> io.BytesIO:
    """
    Download model from cloud
    ref: http://5.9.10.113/67706477/load-pytorch-model-from-s3-bucket
    Args:
        path:
        **kwargs:

    Returns:

    """

    with smart_open.open(path, mode="rb", **kwargs) as fr:
        data = io.BytesIO(fr.read())
    return data


class ChaliceServer(CloudServer):
    INVOKE_METHODS = ("route", "schedule", "on_s3_event")

    def __init__(
        self,
        api_type: str,
        model_path: str,
        model_loader: Callable,
        preprocess_fn: Callable = None,
        postprocess_fn: Callable = None,
        **kwargs,
    ):
        super().__init__(
            api_type,
            model_path=model_path,
            model_loader=model_loader,
            preprocess_fn=preprocess_fn,
            postprocess_fn=postprocess_fn,
            **kwargs,
        )

        self.app = Chalice(app_name=kwargs.get("name", "chitra-server"))

    def predict(self, x) -> dict:
        data_processor = self.data_processor

        if data_processor.preprocess_fn:
            x = data_processor.preprocess(x, **self.preprocess_conf)
        x = self.model(x)
        if data_processor.postprocess_fn:
            x = data_processor.postprocess(x, **self.postprocess_conf)
        return x

    def run(self, invoke_method: str, **kwargs):
        invoke_method = invoke_method.lower()
        if invoke_method not in self.INVOKE_METHODS:
            raise NotImplementedError(
                f"invoke method={invoke_method} not implemented yet. Please select {self.INVOKE_METHODS}"
            )

        if invoke_method == "route":
            route_path = kwargs.get("path", "/predict")
            self.app.route(route_path, methods=["GET"])(self.predict)

        else:
            raise NotImplementedError()