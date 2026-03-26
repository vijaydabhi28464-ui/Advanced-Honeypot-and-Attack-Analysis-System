#!/usr/bin/env python3
"""
Main entry point for the SSH Honeypot server
Run this script from the project root directory
"""

import sys
import os

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

from honeypot.server import start

if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print("\n[-] SSH Honeypot shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Error starting honeypot: {e}")
        sys.exit(1)
