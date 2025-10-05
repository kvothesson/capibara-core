#!/usr/bin/env python3
"""
Advanced example: Data Analysis with Capibara SDK

This example demonstrates more complex usage of Capibara Core SDK
for data analysis tasks with CSV processing and visualization.
"""

import asyncio
import os

from capibara import CapibaraClient


async def main():
    """Main example function."""
    # Initialize Capibara client
    client = CapibaraClient(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    # Example 1: CSV Data Processing
    print("=== CSV Data Processing Example ===")

    csv_response = await client.run(
        prompt="""
        Create a Python script that:
        1. Reads a CSV file called 'sales_data.csv'
        2. Calculates total sales by month
        3. Finds the best-selling product
        4. Generates a summary report
        5. Handles missing data gracefully
        """,
        language="python",
        context={
            "files": ["sales_data.csv"],
            "data": "Sales data with columns: date, product, quantity, price",
        },
        security_policy="moderate",
    )

    print(f"CSV Processing Script ID: {csv_response.script_id}")
    print("\nGenerated Code:")
    print("-" * 50)
    print(csv_response.code)
    print("-" * 50)

    # Example 2: API Integration
    print("\n=== API Integration Example ===")

    api_response = await client.run(
        prompt="""
        Create a Python script that:
        1. Fetches weather data from a public API
        2. Processes the JSON response
        3. Extracts temperature and humidity
        4. Saves the data to a file
        5. Includes error handling for network issues
        """,
        language="python",
        context={
            "environment": "Production environment with network access",
        },
        security_policy="permissive",  # Allow network access
    )

    print(f"API Integration Script ID: {api_response.script_id}")
    print("\nGenerated Code:")
    print("-" * 50)
    print(api_response.code)
    print("-" * 50)

    # Example 3: Data Visualization
    print("\n=== Data Visualization Example ===")

    viz_response = await client.run(
        prompt="""
        Create a Python script that:
        1. Generates sample data (random numbers)
        2. Creates a histogram and scatter plot
        3. Saves plots as PNG files
        4. Uses matplotlib for visualization
        5. Includes proper labels and titles
        """,
        language="python",
        security_policy="moderate",
    )

    print(f"Data Visualization Script ID: {viz_response.script_id}")
    print("\nGenerated Code:")
    print("-" * 50)
    print(viz_response.code)
    print("-" * 50)

    # List all generated scripts
    print("\n=== Generated Scripts ===")
    scripts = await client.list_scripts(limit=10)

    print(f"Total scripts: {scripts.total_count}")
    for script in scripts.scripts:
        print(
            f"- {script.script_id[:12]}... ({script.language}) - {script.prompt[:50]}..."
        )


if __name__ == "__main__":
    asyncio.run(main())
