from .logger import log

def authenticate(username, password, ip):
    log("logs/credentials.log", f"{ip} -> {username}:{password}")
    return False  # Always fail (honeypot)