#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from vast_control import VASTControl

def main():
    # Connection settings
    host = '127.0.0.1'
    port = 21566
    timeout = 2.0

    # Segment settings
    segment_id = 1  # second segment (0-based index)

    # Chunk dimensions (X, Y, Z)
    chunk_size = (2048, 2048, 64)

    # Starting coordinates of chunk
    x_start, y_start, z_start = 0, 0, 0
    x_end = x_start + chunk_size[0] - 1
    y_end = y_start + chunk_size[1] - 1
    z_end = z_start + chunk_size[2] - 1

    # Connect to VAST server
    vc = VASTControl()
    if not vc.connect(host, port, timeout):
        raise RuntimeError("Failed to connect to VAST server")

    # Fetch raw segmentation block as uint16 labels
    raw = vc.get_segment_image_raw(
        miplevel=0,
        minx=x_start, maxx=x_end,
        miny=y_start, maxy=y_end,
        minz=z_start, maxz=z_end
    )

    # Decode raw bytes into numpy array
    # MATLAB reshaping: reshape to (X, Y, Z) then permute axes to (Y, X, Z)
    xdim, ydim, zdim = chunk_size
    arr = np.frombuffer(raw, dtype=np.uint16)
    arr = arr.reshape((xdim, ydim, zdim), order='F')
    arr = np.transpose(arr, (1, 0, 2))  # now arr.shape == (Y, X, Z)

    # Create binary mask for the chosen segment
    mask = (arr == segment_id)

    # Display a middle Z-slice of the mask
    mid_z = zdim // 2
    plt.imshow(mask[:, :, mid_z], cmap='gray')
    plt.title(f"Segment {segment_id} mask at Z={{mid_z}}")
    plt.axis('off')
    plt.show()

    # Disconnect
    vc.disconnect()

if __name__ == '__main__':
    main()
