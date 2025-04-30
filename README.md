# VASTlite_Python-API
Subset of VASTtools functions to export mesh from VAST via Python (without Matlab)
# VASTlite Python API

A collection of scripts and notebooks for fetching segmentation chunks from VASTlite and meshing them in Python.

## Setup
1. **Download this repository**
   Download the repository as zip and extract to your preferred directory

2. **Install Anaconda**  
   Download and install from https://www.anaconda.com/products/distribution

3. **Open Anaconda Prompt**

4. **Create and activate your environment**  
   Replace `VASTlite` with whatever name you prefer:
   ```
   conda create -n VASTlite python=3.10.15 -y
   conda activate VASTlite
   ```

5. **Navigate to the API folder**  
   ```
   cd C:/wherever/VASTlite_PY-API
   ```

6. **Install JupyterLab**  
   ```
   conda install jupyterlab -y
   ```

7. **Launch JupyterLab**  
   ```
   jupyter lab
   ```

## Usage

1. **Open the notebook**  
   In JupyterLab, open the `multicore_mesh_pipeline_final_windows.ipynb` notebook.

2. **Install missing dependencies**  
   Run the first cell. This will install any required packages (e.g. `numpy`, `scikit-image`, `trimesh`, `tqdm`).

3. **Enable VASTlite’s Remote Control API**  
   In VASTlite (v1.5.0), go to **Window → Remote Control API Server**, then tick the “Enable” checkbox.

4. **Fetch and mesh chunks**  
   In the notebook, run the second cell (adjust parameters if needed).  
   This will:
   - Connect to VASTlite via TCP  
   - Download all segmentation chunks  
   - Save them temporarily  
   - Generate per‐chunk meshes and stores them as `.ply` files

5. **Glue chunks together**  
   Finally, run the third cell to merge all chunk meshes into a single `.ply` file.

---

Happy segmenting! 🎉

