from fastapi import FastAPI
from lab01_lib.api.models.iris import PredictRequest, PredictResponse
from lab01_lib.api.inference import load_model, iris_predict

app = FastAPI()


@app.get("/")
def welcome_root():
    return {"message": "Welcome to the ML API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    model = load_model("models/model.joblib")
    prediction = iris_predict(model, request.model_dump())
    return PredictResponse(prediction=prediction)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
