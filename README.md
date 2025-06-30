# TFG Project – From 2D CAD Plans to VR Visualization

This repository contains the complete pipeline for converting architectural floor plans into interactive 3D environments viewable in Virtual Reality (VR).

---

## 📁 Project Structure

```
TFG/
├── 2D-3D/                  # AutoCAD to Blender processing
│   ├── autocad/
│   └── blender/
│   └── README.md
│
├── 3D-VR/                  # Unity project for VR visualization
│   ├── Assets/
│   ├── ProjectSettings/
│   ├── Packages/
│   └── ... (Unity project files)
│
└── README.md               # Global README (this file)
```

---

## 🧱 Part 1: 2D to 3D – From AutoCAD to Blender

This project automates the conversion of architectural floor plans in AutoCAD format (`.dwg`) into 3D models in Blender (`.blend`), enabling their use in interactive environments such as Virtual Reality (VR).

### Project Structure

```
2D-3D/
├── autocad/
│   ├── dwg/
│   │   └── base_plane.dwg          # Input 2D floor plan
│   ├── results/
│   │   └── preprocessed_plane.dxf  # DXF output from AutoCAD
│   └── main.py                     # Python script for AutoCAD automation
│
├── blender/
│   ├── 3Dmodeling.py               # Blender script for 3D model generation
│   ├── main.py                     # Python launcher that runs Blender in background
│   └── results/
│       ├── original.blend          # Pre-reform model
│       └── reformed.blend          # Post-reform model
```

### Requirements

- **Operating system:** Windows (AutoCAD and Blender must be installed)
- **AutoCAD** with COM interface (available in desktop versions)
- **Blender** (installation path is automatically detected via the Windows registry)
- **Python 3.x**
- Additional Python modules:
  - `pywin32`
  - `numpy`
  - `opencv-python`
  - `argparse` (standard library)

Install dependencies (optional):

```bash
pip install pywin32 numpy opencv-python
```

### AutoCAD Processing

The script `autocad/main.py` automates the following tasks:

- Loads the `.dwg` floor plan.
- Explodes each block instance.
- Assigns resulting elements to new layers based on the block name.
- Saves the result as a `.dxf` file.

To run:

```bash
python autocad/main.py
```

The output will be saved as `preprocessed_plane.dxf` inside `autocad/results/`.

### Blender 3D Model Generation

> **Important:** The `.dxf` file must be manually imported into Blender using the built-in **AutoCAD DXF Import** add-on. Enable it in Blender via:  
> `Edit > Preferences > Add-ons > Import-Export: Import AutoCAD DXF Format (.dxf)`

Once imported, the script `blender/3Dmodeling.py` processes the geometry and builds a complete 3D model:

- Wall extrusion
- Door detection and orientation
- Window generation in three stacked parts
- Furniture placement with rotation and dimension calculation
- Floor and ceiling creation
- Light fixture detection

Run:

```bash
python blender/main.py
```

The generated models will be saved in:

```
VR-Piso/Assets/Resources/
├── original.blend
└── reformed.blend
```

### Notes

- Input `.blend` files must be located in `blender/results/`.
- DXF curves must follow a specific naming convention (e.g. `00_A_MUROS_curve_`, `00_A_PUERTAS_curve_`, etc.).
- If furniture orientation fails, ensure the layer `00_Orientacion_curve_` is properly defined in the original CAD drawing.

---

## 🕶️ Part 2: 3D to VR – Unity Visualization

The `3D-VR/` folder contains a complete Unity project designed to load the processed 3D models and enable interactive VR visualization.

### Features

- Switch between **original** and **reformed** layouts
- Choose between **standing** or **wheelchair user** avatars
- Open/close interactive doors
- Trigger functions via in-scene UI panels
- Built with support for OpenXR-compatible headsets

### Requirements

- **Unity version:** `6000.0.41f1`
- **Included Unity packages** (already installed with the project):
  - **OpenXR Plugin**
  - **Unity UI**
  - **XR Hands**
  - **XR Interaction Manager**
  - **XR Plugin Management**

### Setup Instructions

1. Open `3D-VR/` in Unity Hub
2. Wait for dependencies to load (first time only)
3. Press **Play** to run the scene
4. Use the in-scene UI to:
   - Toggle housing layouts
   - Change user perspective
   - Interact with environment

---

## 📖 License

This project is licensed under the GNU General Public License v3.0 – see the [LICENSE](LICENSE) file for details.

