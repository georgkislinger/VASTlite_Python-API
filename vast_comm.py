import socket, struct

class VASTComm:
    """
    Handles low-level VAST protocol framing over TCP.
    """
    MAGIC = b'VAST'
    HEADER_SIZE = 12  # 4-byte magic + 8-byte payload length

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock

    @classmethod
    def connect(cls, host: str, port: int, timeout: float = 1.0) -> 'VASTComm':
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        return cls(sock)

    def disconnect(self) -> None:
        self.sock.close()

    def send(self, msg_num: int, params: bytes = b'') -> None:
        payload_len = 4 + len(params)
        header = self.MAGIC + struct.pack('<Q', payload_len)
        header += struct.pack('<I', msg_num)
        self.sock.sendall(header + params)

    def receive_block(self) -> (int, bytes):
        header = self._recv_exact(self.HEADER_SIZE)
        magic = header[:4]
        if magic != self.MAGIC:
            raise ValueError(f"Invalid magic: {magic}")
        payload_len = struct.unpack('<Q', header[4:12])[0]
        data = self._recv_exact(payload_len)
        code = struct.unpack('<i', data[:4])[0]
        return code, data[4:]

    def _recv_exact(self, n: int) -> bytes:
        buf = b''
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Connection closed unexpectedly")
            buf += chunk
        return buf
