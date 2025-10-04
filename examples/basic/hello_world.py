#!/usr/bin/env python3
"""
Basic example: Hello World with Capibara SDK

This example demonstrates the simplest usage of Capibara Core SDK
to generate and execute a "Hello World" script.
"""

import asyncio
import os
from capibara import CapibaraClient


async def main():
    """Main example function."""
    # Initialize Capibara client
    # Make sure to set OPENAI_API_KEY or GROQ_API_KEY environment variable
    client = CapibaraClient(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        groq_api_key=os.getenv('GROQ_API_KEY'),
    )
    
    # Generate a simple "Hello World" script
    print("Generating Hello World script...")
    
    response = await client.run(
        prompt="Create a simple hello world program that prints 'Hello, Capibara!' with current time and date and a random number and your favorite color",
        language="python",
        execute=True,  # Execute the generated script in Docker
    )
    
    print(f"\nGenerated Script ID: {response.script_id}")
    print(f"LLM Provider: {response.llm_provider}")
    print(f"From Cache: {response.cached}")
    
    print("\nGenerated Code:")
    print("-" * 40)
    print(response.code)
    print("-" * 40)
    
    if response.execution_result:
        result = response.execution_result
        print(f"\nExecution Result:")
        print(f"Success: {result.success}")
        print(f"Exit Code: {result.exit_code}")
        print(f"Execution Time: {result.execution_time_ms}ms")
        print(f"Memory Used: {result.memory_used_mb:.1f}MB")
        
        if result.stdout:
            print(f"\nOutput:")
            print(result.stdout)
        
        if result.stderr:
            print(f"\nError Output:")
            print(result.stderr)


if __name__ == "__main__":
    asyncio.run(main())
