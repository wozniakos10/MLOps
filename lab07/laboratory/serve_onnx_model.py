import os
import time

import onnxruntime as ort
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "sentence-transformers/multi-qa-mpnet-base-cos-v1"
)
input_texts = [
    "Transformers are amazing for natural language processing tasks.",
]

inputs = tokenizer(input_texts, return_tensors="np", truncation=True, padding=True)


# Create input dictionary, in same format as during export
inputs_onnx = {
    "input_ids": inputs["input_ids"],
    "attention_mask": inputs["attention_mask"],
}


model_path = os.getenv("MODEL_PATH")


sess_options = ort.SessionOptions()


# disable for offline mode
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL

# explicitly setup cpu provider as we are testing cpu in that example
session_cpu = ort.InferenceSession(
    model_path, sess_options=sess_options, providers=["CPUExecutionProvider"]
)

inference_times = []
for _ in range(100):
    start = time.time()
    outputs = session_cpu.run(None, inputs_onnx)
    end = time.time()
    inference_times.append(end - start)

mean_inference_time = sum(inference_times) / len(inference_times)
std_inerence_time = (
    sum((x - mean_inference_time) ** 2 for x in inference_times)
    / (len(inference_times) - 1)
) ** 0.5
print(f"Average inference time over 100 runs: {mean_inference_time} seconds")
print(f"Stddev of inference time over 100 runs: {std_inerence_time} seconds")
