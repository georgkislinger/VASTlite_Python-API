#!/usr/bin/env python3
"""
Merge chunked PLY meshes into a single mesh without additional scaling.

Usage:
  python glue_and_scale_mesh.py \
    --input-dir meshes \
    --output merged.ply \
    --tol 1e-6

If the specified output file exists, it will try:
  merged.ply, merged_1.ply, merged_2.ply, etc.
"""

import os
import glob
import argparse
import trimesh

def parse_args():
    parser = argparse.ArgumentParser(description="Merge chunked PLY meshes without scaling")
    parser.add_argument('--input-dir', '-i', required=True,
                        help='Directory containing chunk PLY files')
    parser.add_argument('--output', '-o', default='merged.ply',
                        help='Output filename for merged mesh')
    parser.add_argument('--tol', '-t', type=float, default=1e-6,
                        help='Tolerance for merging duplicate vertices')
    return parser.parse_args()

def unique_path(path):
    """
    If path exists, append _1, _2, ... before extension to find a free filename.
    """
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1
    return new_path

def main():
    args = parse_args()

    # Load chunk meshes
    pattern = os.path.join(args.input_dir, '*.ply')
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No PLY files found in {args.input_dir}")
        return
    print(f"Loading {len(files)} chunk meshes...")
    meshes = [trimesh.load(f, process=False) for f in files]

    # Concatenate meshes
    print("Concatenating meshes...")
    combined = trimesh.util.concatenate(meshes)

    # Merge vertices
    print(f"Merging vertices (tol={args.tol})...")
    combined.merge_vertices(args.tol)

    # Remove duplicate faces
    print("Removing duplicate faces...")
    combined.update_faces(combined.unique_faces())

    # Resolve output path
    out = unique_path(args.output)
    print(f"Exporting merged mesh to {out} ...")
    combined.export(out)
    print("Done!")

if __name__ == '__main__':
    main()
