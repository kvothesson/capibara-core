#!/usr/bin/env python3
"""
Security example: Safe Script Generation with Capibara SDK

This example demonstrates security features and policy enforcement
in Capibara Core SDK.
"""

import asyncio
import os

from capibara import CapibaraClient, SecurityError


async def main():
    """Main example function."""
    # Initialize Capibara client
    client = CapibaraClient(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    # Example 1: Strict Security Policy
    print("=== Strict Security Policy Example ===")

    try:
        strict_response = await client.run(
            prompt="Create a script that reads a file and processes it",
            language="python",
            security_policy="strict",  # Most restrictive policy
        )

        print(f"Strict Policy Script ID: {strict_response.script_id}")
        print("Generated Code (should be safe):")
        print("-" * 50)
        print(strict_response.code)
        print("-" * 50)

    except SecurityError as e:
        print(f"Security Error (expected for dangerous code): {e}")
        if e.violations:
            for violation in e.violations:
                print(f"  - {violation.rule_name}: {violation.message}")

    # Example 2: Attempting Dangerous Operations
    print("\n=== Dangerous Operations Test ===")

    dangerous_prompts = [
        "Create a script that deletes all files in a directory",
        "Generate code that executes system commands",
        "Write a script that opens network connections",
        "Create code that uses eval() to execute strings",
    ]

    for i, prompt in enumerate(dangerous_prompts, 1):
        print(f"\nDangerous Prompt {i}: {prompt}")

        try:
            response = await client.run(
                prompt=prompt,
                language="python",
                security_policy="strict",
            )
            print("  ✓ Script generated (unexpected - should be blocked)")
            print(f"  Script ID: {response.script_id}")

        except SecurityError as e:
            print(f"  ✗ Blocked by security policy: {e}")
            if e.violations:
                for violation in e.violations:
                    print(f"    - {violation.rule_name}: {violation.message}")

    # Example 3: Safe vs Unsafe Code Comparison
    print("\n=== Safe vs Unsafe Code Comparison ===")

    # Safe code
    print("Safe Code Example:")
    safe_response = await client.run(
        prompt="Create a simple calculator that adds two numbers",
        language="python",
        security_policy="moderate",
    )
    print(f"Safe Script ID: {safe_response.script_id}")
    print("Generated Code:")
    print("-" * 30)
    print(safe_response.code)
    print("-" * 30)

    # Example 4: Security Policy Comparison
    print("\n=== Security Policy Comparison ===")

    policies = ["strict", "moderate", "permissive"]

    for policy in policies:
        print(f"\nTesting {policy} policy:")

        try:
            response = await client.run(
                prompt="Create a script that uses the os module to get current directory",
                language="python",
                security_policy=policy,
            )
            print(f"  ✓ Script generated with {policy} policy")
            print(f"  Script ID: {response.script_id}")

        except SecurityError as e:
            print(f"  ✗ Blocked by {policy} policy: {e}")

    # Example 5: Health Check
    print("\n=== System Health Check ===")

    health = await client.health_check()
    print(f"Overall Health: {'✓ Healthy' if health['overall'] else '✗ Unhealthy'}")

    for component, status in health["components"].items():
        if status["healthy"]:
            print(f"  {component}: ✓ Healthy")
        else:
            print(
                f"  {component}: ✗ Unhealthy - {status.get('error', 'Unknown error')}"
            )

    # Example 6: Statistics
    print("\n=== System Statistics ===")

    stats = client.get_stats()

    print("Cache Statistics:")
    cache_stats = stats["cache"]
    print(f"  Hits: {cache_stats['hits']}")
    print(f"  Misses: {cache_stats['misses']}")
    print(f"  Hit Rate: {cache_stats['hit_rate_percent']:.1f}%")

    print("\nLLM Provider Statistics:")
    provider_stats = stats["llm_providers"]
    print(f"  Total Requests: {provider_stats['total_requests']}")
    print(f"  Success Rate: {provider_stats['success_rate']:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
