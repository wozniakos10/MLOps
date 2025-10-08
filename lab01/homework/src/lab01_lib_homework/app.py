from fastapi import FastAPI

from lab01_lib_homework.api.models import PredictRequest, PredictResponse

app = FastAPI()


@app.get("/")
def welcome_root():
    return {"message": "Welcome to the ML API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    prediction = "positive"
    return PredictResponse(prediction=prediction)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
