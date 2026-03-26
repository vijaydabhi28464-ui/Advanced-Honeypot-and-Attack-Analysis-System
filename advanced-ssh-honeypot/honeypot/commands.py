from .logger import log

FAKE_RESPONSES = {
    "ls": "bin  etc  home  var",
    "whoami": "root",
    "uname -a": "Linux honeypot 5.15.0"
}

def handle_command(cmd, ip):
    log("logs/commands.log", f"{ip} -> {cmd}")
    return FAKE_RESPONSES.get(cmd, "command not found")