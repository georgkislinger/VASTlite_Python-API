import struct

def bytes_from_uint32(val: int) -> bytes:
    return b'\x01' + struct.pack('<I', val)

def bytes_from_int32(val: int) -> bytes:
    return b'\x04' + struct.pack('<i', val)

def bytes_from_double(val: float) -> bytes:
    return b'\x02' + struct.pack('<d', val)

def bytes_from_text(text: str) -> bytes:
    return b'\x03' + text.encode('ascii') + b'\x00'

def bytes_from_data(data: bytes) -> bytes:
    return b'\x05' + struct.pack('<I', len(data)) + data
