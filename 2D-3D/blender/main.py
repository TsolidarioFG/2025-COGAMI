import subprocess
import os
import time

def get_blender_path():
    """ Gets the Blender installation path from the Windows registry. """
    command = [
        "powershell", 
        "-Command", 
        'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*" '
        '| Where-Object { $_.DisplayName -match "Blender" } '
        '| Select-Object -ExpandProperty InstallLocation'
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout.strip()

def get_project_root():
    script_path = os.path.abspath(__file__)
    directory_path = os.path.dirname(script_path)
    return os.path.dirname(os.path.dirname(directory_path))


def run_blender_with_script(blend_file, python_script, base_path):
    blender_path = get_blender_path()
    if not blender_path:
        print("Could not run Blender (path not found in registry).")
        return

    blender_exe = os.path.join(blender_path, "blender.exe")
    blend_path = os.path.abspath(blend_file)
    script_path = os.path.abspath(python_script)

    # Build the command:
    cmd = [
        blender_exe,
        "--background",
        blend_path,
        "--python", script_path,
        "--",                                # <-- everything after this goes to sys.argv of the script
        f"--base-path={base_path}"
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    base_path = get_project_root()
    blend_path = os.path.join(base_path, 'tfg', 'blender', 'results', 'original.blend')
    save_path = os.path.join(base_path, 'VR-Piso', 'Assets', 'Resources', 'original.blend')
    
    blend_path2 = os.path.join(base_path, 'tfg', 'blender', 'results', 'reformed.blend')
    save_path2 = os.path.join(base_path, 'VR-Piso', 'Assets', 'Resources', 'reformed.blend')

    script_path = os.path.join(base_path, 'tfg', 'blender', '3Dmodeling.py')

    run_blender_with_script(blend_path, script_path, save_path)
    run_blender_with_script(blend_path2, script_path, save_path2)
