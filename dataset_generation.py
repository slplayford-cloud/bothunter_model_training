#!/usr/bin/env python3

"""
Generate conversational datasets by simulating multi-turn interactions.

This script loads scenario contexts from context_windows.json and simulates
back-and-forth conversations between a BotHunter agent and a target
assistant using the Ollama client. It captures messages from both sides,
records whether the BotHunter flagged the assistant as malicious, and
outputs a structured JSON summary to conversation_output.json.

Key features:
- Loads scenarios from context_windows.json.
- Simulates a configurable number of turns (default: 5) using a local model
    such as `gemma3:12b` via the Ollama API.

NOTE: a larger model is needed for viable results
NOTE: i would suggest gemma3:12b or better

- Saves results including messages per turn and a `flagged_as_malicious`
    indicator for each scenario.

Prerequisites:
- Ollama reachable at http://localhost:11434.
- The `ollama` Python client installed and a compatible local model available.

Usage:
Run the script directly
Adjust context_windows.json, model name, or turn count in the script as
needed for different datasets or experiments.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from ollama import Client


# Configuration constants
DEFAULT_MODEL = 'gemma3:12b'
BOTHUNTER_HOST = 'http://localhost:11434'
EXTERNAL_HOST = 'http://localhost:11434'
DEFAULT_MAX_TURNS = 5


def load_scenarios(filepath: str) -> List[Dict[str, Any]]:
    """
    Load conversation scenarios from a JSON file.
    """
    with open(filepath) as f:
        return json.load(f)

def save_results(results: List[Dict[str, Any]], filepath: str) -> None:
    """
    Save conversation results to a JSON file.
    """
    output = {"scenarios": results}
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved all scenarios to {filepath}")

def get_chat_response(client: Client, model: str, messages: List[Dict[str, str]]) -> str:
    """
    Get a response from the Ollama chat API.
    """
    response = client.chat(model=model, messages=messages, stream=False)
    return response['message']['content']

# TODO - Update is_flagged_malicious to run a real check 
# hopefully integrate our fine tuned model for this
def is_flagged_malicious(response: str) -> bool:
    """
    Check if a response indicates malicious behavior was detected.
    """
    return "FINAL ASSESSMENT: MALICIOUS".lower() in response.lower()

def initialize_messages(hunter_prompt: str, assistant_prompt: str) -> tuple:
    """
    Initialize message histories for both hunter and assistant.
    """
    client_messages = [{"role": "user", "content": hunter_prompt}]
    server_messages = [{"role": "system", "content": assistant_prompt}]
    return client_messages, server_messages

def execute_conversation_turn(
    client: Client,
    server: Client,
    model: str,
    client_messages: List[Dict[str, str]],
    server_messages: List[Dict[str, str]],
    verbose: bool = True
) -> tuple:
    """
    Execute one complete turn of conversation (server responds, then client responds).
    
    Args:
        client: BotHunter client
        server: Assistant server
        model: Model name to use
        client_messages: BotHunter's message history
        server_messages: Assistant's message history
        verbose: Whether to print responses
        
    Returns:
        Tuple of (client_response, server_response, flagged_as_malicious)
    """
    # Server (Assistant) responds
    server_response = get_chat_response(server, model, server_messages)
    if verbose:
        print("----------------------------------------------------")
        print(f"Assistant Bot: {server_response}")
    
    # Update both message histories with server response
    server_messages.append({"role": "assistant", "content": server_response})
    client_messages.append({"role": "user", "content": server_response})
    
    # Client (BotHunter) responds
    client_response = get_chat_response(client, model, client_messages)
    if verbose:
        print("----------------------------------------------------")
        print(f"BotHunter: {client_response}")
    
    # Update both message histories with client response
    client_messages.append({"role": "assistant", "content": client_response})
    server_messages.append({"role": "user", "content": client_response})
    
    # Check if malicious flag was raised
    flagged = is_flagged_malicious(client_response)
    if flagged and verbose:
        print("Malicious bot detected. Stopping conversation.")
    
    return client_response, server_response, flagged

def run_scenario_conversation(
    scenario: Dict[str, Any],
    client: Client,
    server: Client,
    model: str = DEFAULT_MODEL,
    max_turns: int = DEFAULT_MAX_TURNS,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run a complete conversation for a single scenario.
    
    Args:
        scenario: Scenario dictionary with context, hunter, assistant, and malicious fields
        client: BotHunter client
        server: Assistant server
        model: Model name to use
        max_turns: Maximum number of conversation turns
        verbose: Whether to print conversation details
        
    Returns:
        Dictionary with scenario results including all messages and flags
    """
    context_name = scenario["context"]
    hunter_prompt = scenario["hunter"]
    assistant_prompt = scenario["assistant"]
    expected_malicious = scenario["malicious"]
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"SCENARIO: {context_name} (expected malicious: {expected_malicious})")
        print(f"{'='*60}")
    
    client_messages, server_messages = initialize_messages(hunter_prompt, assistant_prompt)
    
    initial_response = get_chat_response(client, model, client_messages)
    if verbose:
        print("----------------------------------------------------")
        print(f"BotHunter: {initial_response}")
    
    client_messages.append({"role": "assistant", "content": initial_response})
    server_messages.append({"role": "user", "content": initial_response})
    
    flagged_as_malicious = False
    
    for turn in range(max_turns):
        _, _, flagged = execute_conversation_turn(
            client, server, model, client_messages, server_messages, verbose
        )
        
        if flagged:
            flagged_as_malicious = True
            break
    
    #get hunter and assistant responses for output
    bot_hunter_responses = {
        f"turn_{i + 1}": msg["content"] 
        for i, msg in enumerate(server_messages) 
        if msg["role"] == "user"
    }
    
    assistant_responses = {
        f"turn_{i + 1}": msg["content"] 
        for i, msg in enumerate(server_messages) 
        if msg["role"] == "assistant"
    }
    
    return {
        "context": context_name,
        "expected_malicious": expected_malicious,
        "flagged_as_malicious": flagged_as_malicious,
        "bot_hunter_responses": bot_hunter_responses,
        "assistant_responses": assistant_responses,
    }

def run_all_scenarios(
    context_file: str = "context_windows.json",
    output_file: str = "conversation_output.json",
    model: str = DEFAULT_MODEL,
    server_host: str = EXTERNAL_HOST,
    client_host: str = BOTHUNTER_HOST,
    max_turns: int = DEFAULT_MAX_TURNS,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Run conversations for all scenarios and save results.
    
    Args:
        context_file: Path to input scenarios JSON
        output_file: Path to output results JSON
        model: Ollama model name
        host: Ollama server host
        max_turns: Maximum conversation turns per scenario
        verbose: Whether to print conversation details
    """

    server = Client(host=server_host)
    client = Client(host=client_host)
    
    scenarios = load_scenarios(context_file)
    
    all_results = []
    for scenario in scenarios:
        result = run_scenario_conversation(
            scenario, client, server, model, max_turns, verbose
        )
        all_results.append(result)
        print(all_results)
    
    save_results(all_results, output_file)
    
    return all_results


def main():
    """Main execution function."""
    run_all_scenarios()


if __name__ == '__main__':
    main()