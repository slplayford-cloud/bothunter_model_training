This directory is reserved for the **LoRA/adapter weights** for the BotHunter
interrogator model.

Workflow (high level):

1. Use `scripts/prepare_interrogator_dataset.py` to generate
   `data/interrogator_train.jsonl` from your recorded conversations (and any
   optional synthetic examples).
2. Fine-tune a LoRA/QLoRA adapter for the same base model you use in Ollama
   (e.g. `gemma3:4b`) using Unsloth, MLX, or another PEFT-compatible stack.
3. Export the adapter in a format Ollama supports:
   - Either a directory containing `adapter_config.json` and `.safetensors`
     weights, or
   - A single `.gguf` adapter file (depending on your tooling and Ollama
     version).
4. Place the exported adapter here, for example:
   - `adapters/bothunter-lora/` (directory of safetensors files), or
   - `adapters/bothunter-lora.gguf`.
5. Point your Modelfile `ADAPTER` directive at the chosen path.

This repository does **not** include the adapter weights themselves; you
generate and manage them outside of version control as needed.

