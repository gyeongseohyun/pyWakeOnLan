import socket

def create_magic_packet(mac_address: str) -> bytes:
    mac_address = mac_address.replace(":", "").replace("-", "")
    mac_bytes = bytes.fromhex(mac_address)
    return b'\xff' * 6 + mac_bytes * 16

def send_magic_packet(ip_address: str, mac_address: str, port: int = 9):
    packet = create_magic_packet(mac_address)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (ip_address, port))