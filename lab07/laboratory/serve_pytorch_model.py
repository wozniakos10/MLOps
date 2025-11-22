import os
import time

import torch
from transformers import AutoConfig, AutoModel, AutoTokenizer

device = "cpu"
tokenizer = AutoTokenizer.from_pretrained(
    "sentence-transformers/multi-qa-mpnet-base-cos-v1"
)
input_texts = [
    "Transformers are amazing for natural language processing tasks.",
]
inputs = tokenizer(input_texts, return_tensors="pt", truncation=True, padding=True).to(
    device
)

model_path = os.getenv("MODEL_PATH")

# Load state_dict
state_dict = torch.load(model_path, map_location=device, weights_only=False)

# Create model WITHOUT loading pretrained weights - just the architecture
config = AutoConfig.from_pretrained("sentence-transformers/multi-qa-mpnet-base-cos-v1")
model = AutoModel.from_config(config)


model.load_state_dict(state_dict, strict=False)
model.to(device)
model.eval()

inference_times = []
for _ in range(100):
    with torch.inference_mode():
        start = time.time()
        outputs = model(**inputs)
        end = time.time()
        inference_times.append(end - start)

mean_inference_time = sum(inference_times) / len(inference_times)
std_inerence_time = (
    sum((x - mean_inference_time) ** 2 for x in inference_times)
    / (len(inference_times) - 1)
) ** 0.5
print(f"Average inference time over 100 runs: {mean_inference_time} seconds")
print(f"Stddev of inference time over 100 runs: {std_inerence_time} seconds")
