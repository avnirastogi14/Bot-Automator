from huggingface_hub import login

# Replace "YOUR_HUGGINGFACE_TOKEN" with your actual token
login(token="")

import torch
from transformers import pipeline

model_id = "meta-llama/Llama-3.2-1B"

pipe = pipeline(
    "text-generation",
    model=model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

pipe("The key to life is")

print()

import discord
print(discord.__version__)
