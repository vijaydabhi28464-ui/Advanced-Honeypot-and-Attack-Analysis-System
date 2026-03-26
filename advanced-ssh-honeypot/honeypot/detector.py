from .logger import log
from collections import defaultdict

attempts = defaultdict(int)

def detect(ip):
    attempts[ip] += 1
    if attempts[ip] >= 5:
        log("logs/attacks.log", f"Brute-force detected from {ip}")