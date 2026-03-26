import socket
import threading
import paramiko
import logging
import sys
import warnings
from .auth import authenticate
from .commands import handle_command
from .detector import detect
from .config import HOST, PORT

# Suppress warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

# Suppress paramiko logging
logging.getLogger("paramiko").setLevel(logging.CRITICAL)
logging.getLogger("paramiko.transport").setLevel(logging.CRITICAL)

host_key = paramiko.RSAKey.generate(2048)

class HoneypotServer(paramiko.ServerInterface):
    def __init__(self, ip):
        self.ip = ip
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        """Log authentication attempts and always fail"""
        authenticate(username, password, self.ip)
        detect(self.ip)
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"

    def check_channel_request(self, kind, chanid):
        """Accept all channel requests"""
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        """Accept shell requests"""
        self.event.set()
        return paramiko.PARAMIKO_MSG_CHANNEL_SUCCESS

    def check_channel_exec_request(self, channel, command):
        """Handle command execution"""
        try:
            cmd_str = command.decode() if isinstance(command, bytes) else command
            response = handle_command(cmd_str, self.ip)
            channel.send(response.encode() + b"\r\n")
            channel.send_exit_status(0)
        except:
            pass
        return True

def client_handler(client, addr):
    """Handle SSH client connections"""
    ip = addr[0]
    transport = None
    
    try:
        # Create transport
        transport = paramiko.Transport(client)
        transport.add_server_key(host_key)
        
        # Start server
        server = HoneypotServer(ip)
        try:
            transport.start_server(server=server, event=server.event)
        except Exception as e:
            logging.debug(f"Server start error: {str(e)[:80]}")
            return
        
        # Handle channels
        while transport.is_active():
            try:
                chan = transport.accept(0.1)
                if chan is None:
                    continue
                
                try:
                    # Send welcome
                    chan.send(b"Welcome to Ubuntu 20.04 LTS\r\n")
                    chan.send(b"$ ")
                    
                    # Command loop
                    while transport.is_active() and chan.is_active():
                        try:
                            data = chan.recv(1024)
                            if not data:
                                break
                            
                            cmd = data.decode('utf-8', errors='ignore').strip()
                            if cmd:
                                response = handle_command(cmd, ip)
                                chan.send((response + "\r\n$ ").encode())
                        except socket.timeout:
                            continue
                        except:
                            break
                            
                except:
                    pass
                finally:
                    try:
                        chan.close()
                    except:
                        pass
                        
            except socket.timeout:
                continue
            except:
                break
                
    except (socket.error, paramiko.SSHException):
        # Suppress socket errors - these are expected when clients disconnect
        pass
    except Exception as e:
        logging.debug(f"Unexpected error: {str(e)[:80]}")
    finally:
        try:
            if transport:
                transport.close()
        except:
            pass
        try:
            client.close()
        except:
            pass

def start():
    """Start SSH honeypot"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((HOST, PORT))
        sock.listen(100)
        logging.info(f"SSH Honeypot running on {HOST}:{PORT}")

        while True:
            try:
                client, addr = sock.accept()
                client.settimeout(20)
                thread = threading.Thread(target=client_handler, args=(client, addr), daemon=True)
                thread.start()
            except KeyboardInterrupt:
                logging.info("Shutting down...")
                break
            except Exception as e:
                logging.debug(f"Accept error: {str(e)[:80]}")
                
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        sys.exit(1)
    finally:
        try:
            sock.close()
        except:
            pass
        logging.info("Server stopped")

if __name__ == "__main__":
    start()