# TFG Project – 3D Model Generation from 2D CAD Plans

This project automates the conversion of architectural floor plans in AutoCAD format (`.dwg`) into 3D models in Blender (`.blend`), enabling their use in interactive environments such as Virtual Reality (VR).

## Project Structure

```
TFG/
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

---

## 1. Requirements

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

---

## 2. AutoCAD Processing

The script `autocad/main.py` automates the following tasks:

- Loads the `.dwg` floor plan.
- Explodes each block instance.
- Assigns resulting elements to new layers based on the block name.
- Saves the result as a `.dxf` file.

### Run it with:

```bash
python autocad/main.py
```

The output will be saved as `preprocessed_plane.dxf` inside `autocad/results/`.

---

## 3. Blender 3D Model Generation

> **Important:** The `.dxf` file must be manually imported into Blender using the built-in **AutoCAD DXF Import** add-on. Make sure this add-on is enabled in Blender via:  
> `Edit > Preferences > Add-ons > Import-Export: Import AutoCAD DXF Format (.dxf)`

Once imported, the script `blender/3Dmodeling.py` processes the geometry and builds a complete 3D model:

- Wall extrusion
- Door detection and orientation
- Window generation in three stacked parts
- Furniture placement with rotation and dimension calculation
- Floor and ceiling creation
- Light fixture detection

### To execute it:

Run `blender/main.py` to launch Blender in background mode for both `.blend` scenes:

```bash
python blender/main.py
```

The generated models will be saved in:

```
VR-Piso/Assets/Resources/
├── original.blend
└── reformed.blend
```

---

## 4. Notes

- Input `.blend` files must be located in `blender/results/`.
- DXF curves must follow a specific naming convention (e.g. `00_A_MUROS_curve_`, `00_A_PUERTAS_curve_`, etc.).
- If furniture orientation fails, ensure the layer `00_Orientacion_curve_` is properly defined in the original CAD drawing.

---

## 5. License

This project was developed as part of a Bachelor’s Thesis and is intended for academic use only. Contact the author for more information or permission for reuse.
