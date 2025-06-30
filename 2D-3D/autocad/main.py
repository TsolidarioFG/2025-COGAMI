import pythoncom
import win32com.client
import os


def getProjectRoot():
    script_path = os.path.abspath(__file__)
    directory_path = os.path.dirname(script_path)
    return os.path.dirname(os.path.dirname(directory_path))


def process_dwg(dwg_path, save_path):
    pythoncom.CoInitialize()

    # Start AutoCAD
    acad = win32com.client.Dispatch("AutoCAD.Application")
    acad.Visible = False

    doc = acad.Documents.Open(dwg_path)
    ms = doc.ModelSpace
    layers = doc.Layers

    counter = 1
    objects_to_delete = []

    for obj in ms:
        if obj.ObjectName == "AcDbBlockReference":
            try:
                base_name = obj.EffectiveName
                layer_name = f"{base_name}_{counter}"

                if not layer_exists(layers, layer_name):
                    layers.Add(layer_name)

                elements = obj.Explode()

                # Assign layer to elements
                for e in elements:
                    e.Layer = layer_name

                objects_to_delete.append(obj)
                counter += 1

            except Exception as e:
                print(f"Error processing a block: {e}")

    # Delete original blocks
    for o in objects_to_delete:
        o.Delete()

    doc.SaveAs(save_path, 25)  # 25 is the DXF 2018 file type

    doc.Close(False)
    acad.Quit()

    print("File processed and saved.")

def layer_exists(layers, name):
    for l in layers:
        if l.Name == name:
            return True
    return False
if __name__ == "__main__":
    base_path = getProjectRoot()
    input_path = os.path.join(base_path, 'tfg', 'autocad', 'dwg', 'base_plane.dwg')
    output_path = os.path.join(base_path, 'tfg', 'autocad', 'results', 'preprocessed_plane.')

    process_dwg(input_path, output_path)

