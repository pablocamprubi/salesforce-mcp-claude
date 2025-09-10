#!/usr/bin/env python3
"""
Main entry point for the Salesforce MCP server when run as a module.
Usage: python -m salesforcemcp
"""

from .server import run
import asyncio

if __name__ == "__main__":
    asyncio.run(run())
