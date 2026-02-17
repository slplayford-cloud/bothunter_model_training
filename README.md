# BotHunterX model training

Generate labeled conversational datasets by simulating multi-turn interactions between a `BotHunter` probe agent and a target assistant using Ollama.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have ollama model downloaded (e.g., `gemma3:12b`):
```bash
ollama pull gemma3:12b
```

3. Run the generator:
```bash
./dataset_generation.py
```

## Files

- `dataset_generation.py` — main script
- `context_windows.json` — input scenarios (define `context`, `hunter`, `assistant`, `malicious`)
- `conversation_output.json` — generated dataset

## Configuration

Edit `dataset_generation.py` to customize:
- **Model**: DEFAULT_MODEL
- **Turns**: MAX_TURNS
- **Host**: update *_HOST
    - WILL NEED TO UPDATE:
        - BOTHUNTER_HOST
        - EXTERNAL_HOST

## TODO/NEXT STEPS

- Edit the ollama **modelfile** to inject our customized prompt -- may prevent hallucination
- More powerful spec hardware?
    - Fine tuning LoRa model
    - improve prompting / conversational flow / structuring of responses
    - more advanced bad bots?

- Can we give bots access to processes and execution?