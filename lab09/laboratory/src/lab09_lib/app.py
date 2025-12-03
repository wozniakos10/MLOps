from fastapi import FastAPI, HTTPException

from lab09_lib.api.inference import load_joblib_model, load_sentence_transformer_model, predict_sentiment
from lab09_lib.api.models import PredictRequest, PredictResponse

app = FastAPI()

# Different approaches for loading models in FastAPI. Right now following Simple Approach
##https://apxml.com/courses/fastapi-ml-deployment/chapter-3-integrating-ml-models/loading-models-fastapi


sentence_transformer = load_sentence_transformer_model()
classifier = load_joblib_model()


@app.get("/")
def welcome_root():
    return {"message": "Welcome to the ML API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if sentence_transformer is None or classifier is None:
        raise HTTPException(status_code=503, detail="Model is not available")

    prediction = predict_sentiment(sentence_transformer, classifier, request.model_dump())
    return PredictResponse(prediction=prediction)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
