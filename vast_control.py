from typing import List, Dict
from vast_comm import VASTComm
from vast_param import bytes_from_uint32
from vast_parser import parse_payload, decode_rle16, rle_count_unique

class VASTControl:
    """
    High-level API for segmentation-related VAST commands.
    """
    GETNUMBEROFSEGMENTS   = 2
    GETSEGMENTDATA        = 3
    GETALLSEGMENTDATA     = 14
    GETSEGIMAGERAW        = 20
    GETSEGIMAGERLE        = 21
    GETSEGIMAGERLEIMMEDIATE = 25

    def __init__(self):
        self.comm = None

    def connect(self, host: str, port: int, timeout: float = 1.0) -> bool:
        self.comm = VASTComm.connect(host, port, timeout)
        return True

    def disconnect(self) -> None:
        if self.comm:
            self.comm.disconnect()
            self.comm = None

    def get_number_of_segments(self) -> int:
        self.comm.send(self.GETNUMBEROFSEGMENTS)
        code, payload = self.comm.receive_block()
        if code != 1:
            raise RuntimeError(f"Error {code}")
        return parse_payload(payload)['uints'][0]

    def get_segment_data(self, segment_id: int) -> Dict[str, List]:
        params = bytes_from_uint32(segment_id)
        self.comm.send(self.GETSEGMENTDATA, params)
        code, payload = self.comm.receive_block()
        if code != 1:
            raise RuntimeError(f"Error {code}")
        return parse_payload(payload)

    def get_all_segment_data(self) -> Dict[str, List]:
        self.comm.send(self.GETALLSEGMENTDATA)
        code, payload = self.comm.receive_block()
        if code != 1:
            raise RuntimeError(f"Error {code}")
        return parse_payload(payload)

    def get_segment_image_raw(self,
                              miplevel: int,
                              minx: int, maxx: int,
                              miny: int, maxy: int,
                              minz: int, maxz: int) -> bytes:
        args = [miplevel, minx, maxx, miny, maxy, minz, maxz]
        params = b''.join(bytes_from_uint32(a) for a in args)
        self.comm.send(self.GETSEGIMAGERAW, params)
        code, payload = self.comm.receive_block()
        if code != 1:
            raise RuntimeError(f"Error {code}")
        return payload

    def get_segment_image_rle(self,
                              miplevel: int,
                              minx: int, maxx: int,
                              miny: int, maxy: int,
                              minz: int, maxz: int,
                              immediate: bool = False) -> bytes:
        args = [miplevel, minx, maxx, miny, maxy, minz, maxz, int(immediate)]
        params = b''.join(bytes_from_uint32(a) for a in args)
        cmd = self.GETSEGIMAGERLEIMMEDIATE if immediate else self.GETSEGIMAGERLE
        self.comm.send(cmd, params)
        code, payload = self.comm.receive_block()
        if code != 1:
            raise RuntimeError(f"Error {code}")
        return payload

    def get_segment_image_rle_decoded(self, *args, **kwargs) -> List[int]:
        data = self.get_segment_image_rle(*args, **kwargs)
        return decode_rle16(data)

    def get_segment_image_rle_count_unique(self, *args, **kwargs) -> Dict[int, int]:
        decoded = self.get_segment_image_rle_decoded(*args, **kwargs)
        return rle_count_unique(decoded)
# Add at top of vast_control.py, alongside the other constants:
    GETINFO = 1

# Then, inside the VASTControl class:
    def get_info(self) -> dict:
        """
        Fetches general volume info, including physical voxel size.
        Returns a dict with keys:
          datasizex, datasizey, datasizez,
          voxelsizex, voxelsizey, voxelsizez,
          cubesizex, cubesizey, cubesizez,
          currentviewx, currentviewy, currentviewz,
          nrofmiplevels
        """
        # Send GETINFO command
        self.comm.send(self.GETINFO)
        code, payload = self.comm.receive_block()
        if code != 1:
            raise RuntimeError(f"GETINFO error {code}")
        parsed = parse_payload(payload)
        u = parsed['uints']
        d = parsed['doubles']
        i = parsed['ints']
        return {
            'datasizex'     : u[0],
            'datasizey'     : u[1],
            'datasizez'     : u[2],
            'voxelsizex'    : d[0],
            'voxelsizey'    : d[1],
            'voxelsizez'    : d[2],
            'cubesizex'     : u[3],
            'cubesizey'     : u[4],
            'cubesizez'     : u[5],
            'currentviewx'  : i[0],
            'currentviewy'  : i[1],
            'currentviewz'  : i[2],
            'nrofmiplevels' : u[6]
        }
