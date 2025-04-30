#!/usr/bin/env python3
"""
Mip-aware pipeline that closes only the overall segment volume extremes (X, Y, Z),
dynamically creates a new TMP folder if the default is not empty, correctly
scales XY based on MIP level, and skips uniform chunks to avoid marching_cubes errors.

Usage:
  python multicore_mesh_pipeline_skip_uniform.py \
    --segment 1 --chunk 256 256 32 --overlap 10 --mip 4
"""

import os
import argparse
import numpy as np
from multiprocessing import Pool
from vast_control import VASTControl
from vast_parser import decode_rle16
from skimage import measure
from tqdm import tqdm
import trimesh

def parse_args():
    p = argparse.ArgumentParser(description="Mip-aware pipeline with edge padding, correct MIP scaling, and skip uniform chunks")
    p.add_argument('--host',    default='127.0.0.1')
    p.add_argument('--port',    type=int, default=22081)
    p.add_argument('--segment', type=int, default=1)
    p.add_argument('--chunk',   type=int, nargs=3, default=[256,256,32], metavar=('X','Y','Z'))
    p.add_argument('--overlap', type=int, default=10)
    p.add_argument('--mip',     type=int, default=0, help="MIP level (reduces XY by 2^MIP)")
    p.add_argument('--workers', type=int, default=os.cpu_count())
    p.add_argument('--no-close', action='store_true', help="disable all padding")
    return p.parse_args()

def clamp3(x0,x1,y0,y1,z0,z1, mx,my,mz):
    return (max(0,x0), min(x1,mx),
            max(0,y0), min(y1,my),
            max(0,z0), min(z1,mz))

def make_clean_tmp(base="tmp_dbg"):
    name = base
    i = 1
    while os.path.exists(name) and os.listdir(name):
        name = f"{base}_{i}"
        i += 1
    os.makedirs(name, exist_ok=True)
    return name

def fetch_subvolume(vc, seg, mip, rng):
    x0,x1,y0,y1,z0,z1 = clamp3(*rng, *DATA_MAX)
    rle = vc.get_segment_image_rle(mip, x0, x1, y0, y1, z0, z1, immediate=False)
    if isinstance(rle, list):
        rle = bytes(rle)
    arr = np.array(decode_rle16(rle), dtype=np.uint16)
    sx,sy,sz = x1-x0+1, y1-y0+1, z1-z0+1
    block = arr.reshape((sx,sy,sz), order='F').transpose(1,0,2)
    mask = (block == seg).astype(np.uint8)
    out = os.path.join(TMP, f"mask_{x0}_{y0}_{z0}.npy")
    np.save(out, mask)
    return (x0,y0,z0), mask.shape, out

def mesh_subvolume(args):
    (x0,y0,z0), (sy,sx,sz), path, pad_flags, mesh_dir, vox, mip = args
    mask = np.load(path)
    os.remove(path)
    if mask.min() == mask.max():
        return None

    pad_x0, pad_x1, pad_y0, pad_y1, pad_z0, pad_z1 = pad_flags
    if pad_x0: mask = np.pad(mask, ((0,0),(1,0),(0,0)), constant_values=0); x0-=1
    if pad_x1: mask = np.pad(mask, ((0,0),(0,1),(0,0)), constant_values=0)
    if pad_y0: mask = np.pad(mask, ((1,0),(0,0),(0,0)), constant_values=0); y0-=1
    if pad_y1: mask = np.pad(mask, ((0,1),(0,0),(0,0)), constant_values=0)
    if pad_z0: mask = np.pad(mask, ((0,0),(0,0),(1,0)), constant_values=0); z0-=1
    if pad_z1: mask = np.pad(mask, ((0,0),(0,0),(0,1)), constant_values=0)

    verts, faces, _, _ = measure.marching_cubes(mask, level=0.5, spacing=(1,1,1))
    verts = verts[:, [1,0,2]]

    mip_scale = 1 << mip
    vx, vy, vz = vox
    verts[:,0] *= mip_scale; verts[:,1] *= mip_scale
    offset = np.array([x0*mip_scale, y0*mip_scale, z0], dtype=float)
    verts += offset
    verts *= [vx, vy, vz]

    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    out = os.path.join(mesh_dir, f"mesh_{x0}_{y0}_{z0}.ply")
    mesh.export(out)
    return out

if __name__=="__main__":
    args = parse_args()
    HOST,PORT = args.host, args.port
    SEG = args.segment
    CX,CY,CZ = args.chunk
    OL = args.overlap
    MIP = args.mip
    W = args.workers
    DISABLE = args.no_close

    TMP = make_clean_tmp("tmp_dbg")
    MESH = os.path.join(TMP,"meshes"); os.makedirs(MESH, exist_ok=True)

    vc = VASTControl()
    if not vc.connect(HOST, PORT, timeout=2):
        raise RuntimeError("Cannot connect")
    meta = vc.get_segment_data(SEG)
    info = vc.get_info()
    vc.disconnect()

    dsx,dsy,dsz = info['datasizex'],info['datasizey'],info['datasizez']
    voxels = (info['voxelsizex'],info['voxelsizey'],info['voxelsizez'])
    print("=== VOLUME INFO ===")
    print(f"Full-res dims: x={dsx}, y={dsy}, z={dsz}")
    print(f"MIP {MIP}:       x={(dsx>>MIP)}, y={(dsy>>MIP)}, z={dsz}")
    print(f"Voxel size:     x={voxels[0]}, y={voxels[1]}, z={voxels[2]}")
    x0f,y0f,z0f = meta['ints'][3],meta['ints'][4],meta['ints'][5]
    x1f,y1f,z1f = meta['ints'][6],meta['ints'][7],meta['ints'][8]
    print("=== SEGMENT BBOX ===")
    print(f"Full-res: min=({x0f},{y0f},{z0f}), max=({x1f},{y1f},{z1f})")
    x0m,y0m = x0f>>MIP, y0f>>MIP; x1m,y1m = x1f>>MIP, y1f>>MIP; z0m,z1m = z0f,z1f
    print(f"MIP {MIP}:     min=({x0m},{y0m},{z0m}), max=({x1m},{y1m},{z1m})")

    max_x = (dsx>>MIP)-1; max_y = (dsy>>MIP)-1; max_z = dsz-1
    DATA_MAX = (max_x, max_y, max_z)
    sx_step = CX - 2*OL; sy_step = CY - 2*OL; sz_step = CZ - 2*OL
    ranges = [(x, min(x+CX-1,x1m), y, min(y+CY-1,y1m), z, min(z+CZ-1,z1f))
              for x in range(x0m,x1m+1,sx_step)
              for y in range(y0m,y1m+1,sy_step)
              for z in range(z0m,z1f+1,sz_step)]
    print(f"Total chunks: {len(ranges)}")

    vc.connect(HOST, PORT, timeout=2)
    fetched = [fetch_subvolume(vc, SEG, MIP, r) for r in tqdm(ranges, desc="Fetching")]
    vc.disconnect()

    tasks=[]
    for item in fetched:
        if item is None: continue
        (x0,y0,z0),shape,path = item
        pad_x0=(x0==x0m and not DISABLE)
        pad_x1=((x0+shape[1]-1)==x1m and not DISABLE)
        pad_y0=(y0==y0m and not DISABLE)
        pad_y1=((y0+shape[0]-1)==y1m and not DISABLE)
        pad_z0=(z0==z0m and not DISABLE)
        pad_z1=((z0+shape[2]-1)==z1f and not DISABLE)
        pad_flags=(pad_x0,pad_x1,pad_y0,pad_y1,pad_z0,pad_z1)
        tasks.append(((x0,y0,z0),shape,path,pad_flags,MESH,voxels,MIP))

    with Pool(W) as pool:
        _ = list(tqdm(pool.imap(mesh_subvolume,tasks), total=len(tasks), desc="Meshing"))

    print("=== DONE ===")
    print("Masks in:",TMP)
    print("Meshes in:",MESH)
