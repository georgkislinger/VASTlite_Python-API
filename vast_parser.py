import struct
from collections import Counter
from typing import List, Dict, Any

def parse_payload(data: bytes) -> Dict[str, List[Any]]:
    result = {'uints': [], 'ints': [], 'doubles': [], 'texts': [], 'raw': [], 'uint64s': []}
    idx = 0
    length = len(data)
    while idx < length:
        dtype = data[idx]
        if dtype == 1:
            val = struct.unpack('<I', data[idx+1:idx+5])[0]
            result['uints'].append(val)
            idx += 5
        elif dtype == 2:
            val = struct.unpack('<d', data[idx+1:idx+9])[0]
            result['doubles'].append(val)
            idx += 9
        elif dtype == 3:
            end = data.find(b'\x00', idx+1)
            if end == -1:
                end = length
            text = data[idx+1:end].decode('ascii', errors='ignore')
            result['texts'].append(text)
            idx = end + 1
        elif dtype == 4:
            val = struct.unpack('<i', data[idx+1:idx+5])[0]
            result['ints'].append(val)
            idx += 5
        elif dtype == 5:
            raw_len = struct.unpack('<I', data[idx+1:idx+5])[0]
            raw = data[idx+5:idx+5+raw_len]
            result['raw'].append(raw)
            idx += 5 + raw_len
        elif dtype == 6:
            val = struct.unpack('<Q', data[idx+1:idx+9])[0]
            result['uint64s'].append(val)
            idx += 9
        else:
            break
    return result

def decode_rle16(data: bytes) -> List[int]:
    count = len(data) // 2
    arr = struct.unpack('<' + 'H'*count, data)
    out = []
    for i in range(0, count, 2):
        val, num = arr[i], arr[i+1]
        out.extend([val] * num)
    return out

def rle_count_unique(decoded: List[int]) -> Dict[int, int]:
    return dict(Counter(decoded))
