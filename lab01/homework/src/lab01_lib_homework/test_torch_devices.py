import torch

if torch.cuda.is_available():
    print("CUDA is available. GPU will be used.")
elif torch.backends.mps.is_available():
    print("MPS is available. Apple Silicon GPU will be used.")
else:
    print("CUDA and MPS are not available. CPU will be used.")
