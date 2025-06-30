import bpy
import os
import re
import sys
import cv2
import argparse
import numpy as np
from math import radians, atan2, degrees
from mathutils import Vector, Euler

# ============================
# GENERAL FUNCTIONS
# ============================

def saveBlend(savePath):
    bpy.ops.wm.save_as_mainfile(filepath=savePath)
    print(f"File saved at: {savePath}")
    
def parseNames():
    suffix = "_curve_"

    for objItem in bpy.data.objects:
        if objItem.type != 'CURVE' or not objItem.name.endswith(suffix) or objItem.name.startswith("00_"):
            continue

        # Name without the "_curve_" suffix
        baseName = objItem.name[:-len(suffix)]

        newName = baseName.split("_", 1)[0]
            
        if objItem.name != newName:
            print(f"Renaming '{objItem.name}' → '{newName}'")
            objItem.name = newName








# ============================
# SHARED FUNCTIONS
# ============================

def applyCubeUVUnwrap(obj):
    """
    Applies automatic UV unwrap to the mesh object:
      - method='SMART': Smart UV Project (default)
      - method='CUBE' : Cube Projection
      - method='ANGLE': Angle-Based Unwrap after marking seams on sharp edges
    """
    if not obj or obj.type != 'MESH':
        print(f"[UV] Invalid object or not a mesh: {obj}")
        return

    # Prepare selection
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Enter Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    bpy.ops.uv.cube_project(
        cube_size=1.0,
        correct_aspect=True,
        scale_to_bounds=True
    )
        
    # Return to Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"[UV] Unwrap (CUBE) applied to '{obj.name}'.")


def convertCurveToMesh(objectName):
    meshObj = bpy.data.objects.get(objectName)
    if not meshObj:
        print(f"No object found with name '{objectName}'.")
        return None
    bpy.ops.object.select_all(action='DESELECT')
    meshObj.select_set(True)
    bpy.context.view_layer.objects.active = meshObj
    bpy.ops.object.convert(target='MESH')
    print(f"The curve '{objectName}' has been successfully converted to Mesh.")
    return meshObj


def separateByLooseParts(meshObj):
    if not meshObj:
        return []
    bpy.ops.object.select_all(action='DESELECT')
    meshObj.select_set(True)
    bpy.context.view_layer.objects.active = meshObj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    baseName = meshObj.name
    newObjects = [o for o in bpy.context.scene.objects 
                  if o.name == baseName or o.name.startswith(baseName + ".")]
    print(f"{len(newObjects)} objects have been created from '{baseName}'.")
    return newObjects


def extrudeInZ(meshObj, height=6.0):
    if not meshObj:
        return
    bpy.ops.object.select_all(action='DESELECT')
    meshObj.select_set(True)
    bpy.context.view_layer.objects.active = meshObj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, height)})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"'{meshObj.name}' has been extruded {height} units in Z.")


def recalcNormals(meshObj):
    bpy.ops.object.select_all(action='DESELECT')
    meshObj.select_set(True)
    bpy.context.view_layer.objects.active = meshObj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Normals recalculated for '{meshObj.name}'.")


def getExtremePoints(obj):
    """
    Uses OpenCV to calculate the minimum rotated bounding box of the object in the XY plane.
    Returns 4 points (Vector) in global coordinates with constant Z.
    """
    puntos3D = [obj.matrix_world @ v.co for v in obj.data.vertices]
    puntos2D = np.array([[v.x, v.y] for v in puntos3D], dtype=np.float32)

    rect = cv2.minAreaRect(puntos2D)    # center, (w, h), angle
    box = cv2.boxPoints(rect)           # 4 corners in order
    box = np.array(box)

    z = float(np.mean([v.z for v in puntos3D]))

    corners = [Vector((x, y, z)) for x, y in box]

    print("\nRotated bounding box points (OpenCV):")
    for i, p in enumerate(corners):
        print(f"  Corner {i+1}: {p}")

    return corners








# ============================
# FUNCTIONS FOR WALLS
# ============================

def mainWalls():
    wallsName = "00_A_MUROS_curve_"
    wallsObj = bpy.data.objects.get(wallsName)
    if wallsObj:
        mergeVerticesByDistance(wallsObj)
        walls = separateByLooseParts(wallsObj)
        # Extrude and recalculate normals for each part
        for partObj in walls:
            extrudeInZ(partObj, height=2.70)
        for partObj in walls:
            recalcNormals(partObj)
            applyCubeUVUnwrap(partObj)
    else:
        print("Could not process the wall curve.")


def mergeVerticesByDistance(meshObj, threshold=0.0001):
    if not meshObj:
        print("No valid object was provided.")
        return
    bpy.ops.object.select_all(action='DESELECT')
    meshObj.select_set(True)
    bpy.context.view_layer.objects.active = meshObj
    bpy.ops.object.editmode_toggle()  # Enter Edit Mode
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=threshold)
    print(f"Vertices in '{meshObj.name}' have been merged with threshold={threshold}.")
    bpy.ops.object.editmode_toggle()  # Return to Object Mode









# ============================
# FUNCTIONS FOR DOORS
# ============================
def groupAndExtrudeFramesPerDoor(doors, smallObjects, height=2.0):
    """
    For each door, finds nearby frames with numeric suffix > 2,
    groups them, joins them, and extrudes them.
    """
    framesPerDoor = [[] for _ in doors]

    # Filter only frames with suffix .xxx > 2
    frames = []
    for o in smallObjects:
        m = re.search(r"\.(\d+)$", o.name)
        if m and int(m.group(1)) > 2:
            frames.append(o)

    # Assign each frame to the nearest door
    for frame in frames:
        bpy.ops.object.select_all(action='DESELECT')
        frame.select_set(True)
        bpy.context.view_layer.objects.active = frame
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        min_dist = float('inf')
        door_idx = -1
        for i, door in enumerate(doors):
            d = (door.location - frame.location).length
            if d < min_dist:
                min_dist = d
                door_idx = i
        framesPerDoor[door_idx].append(frame)

    # For each group of frames
    for group in framesPerDoor:
        if not group:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
        finalFrame = bpy.context.active_object
        extrudeInZ(finalFrame, height=height)
        recalcNormals(finalFrame)
        applyCubeUVUnwrap(finalFrame)


def mainDoors():
    doorsName = "00_A_PUERTAS_curve_"
    doorsObj = convertCurveToMesh(doorsName)
    if doorsObj:
        parts = separateByLooseParts(doorsObj)
        # Rename the "large" parts as PUERTA (threshold >= 0.5)
        renameLargeParts(parts, threshold=0.5)
        # Split into two groups: "doors" (renamed) and "smallObjects"
        doors = [o for o in parts if o.name.startswith("PUERTA")]
        smallObjects = [o for o in parts if not o.name.startswith("PUERTA")]
        # For each PUERTA object, adjust the origin to the vertex closest to any of the smallObjects
        for door in doors:
            setOriginToClosestVertex(door, smallObjects)
            float_angle = computeDoorAngle(door)
            door.name = f"{door.name}_{float_angle}R"
            print(f"Door '{door.name}': oriented angle = {float_angle}°")
        # Extrude all objects (doors and smallObjects) 2.03 units in Z
        for o in doors + smallObjects:
            extrudeInZ(o, height=2.03)
        for o in doors + smallObjects:
            recalcNormals(o)
            applyCubeUVUnwrap(o)
    else:
        print("Could not process the door curve.")


def computeDoorAngle(doorObj):
    """
    After moving the origin of doorObj, computes the angle (0–360)
    using the bisector between the two vectors pointing from the origin
    to the two closest vertices.
    """
    origin_world = doorObj.matrix_world.translation
    tol = 1e-6

    # Collect all vectors and their distances to the origin (excluding the origin itself)
    vecs = []
    for v in doorObj.data.vertices:
        world_v = doorObj.matrix_world @ v.co
        vec = world_v - origin_world
        dist_sq = vec.length_squared
        if dist_sq < tol:
            continue
        vecs.append((dist_sq, vec))

    if not vecs:
        return 0.0

    # Sort by ascending distance
    vecs.sort(key=lambda x: x[0])

    # If only one vector, use classic method
    if len(vecs) == 1:
        dir_vec = vecs[0][1]
    else:
        # Take the two closest vectors
        v1 = vecs[0][1].normalized()
        v2 = vecs[1][1].normalized()
        # Bisector: normalized sum of vectors
        dir_vec = (v1 + v2).normalized()

    # Compute angle in the X-Y plane and normalize to [0,360)
    angle = (degrees(atan2(dir_vec.y, dir_vec.x)) + 360.0) % 360.0
    return round(angle, 2)


def renameLargeParts(objects, threshold=0.5):
    """
    Renames objects in the list whose maximum bounding box dimension
    is >= 'threshold' to "PUERTA". If there are multiple, adds a numeric suffix.
    """
    counter = 1
    for objItem in objects:
        maxDim = max(objItem.dimensions)
        if maxDim >= threshold:
            newName = "PUERTA" if counter == 1 else f"PUERTA.{counter:03d}"
            print(f"Renaming '{objItem.name}' to '{newName}' (max dimension: {maxDim:.3f} >= {threshold})")
            objItem.name = newName
            counter += 1


def setOriginToClosestVertex(obj, smallObjects):
    """
    For the object 'obj' (type DOOR), finds the vertex in world space
    closest to any vertex of the objects in 'smallObjects' and sets
    the origin of 'obj' to that vertex.
    """
    if not obj or not obj.data.vertices:
        print(f"The object '{obj.name}' has no vertices.")
        return
    if not smallObjects:
        print(f"There are no small objects to compare; origin change skipped for '{obj.name}'.")
        return

    bestWorldCoord = None
    bestDistance = None
    for v in obj.data.vertices:
        worldCoord = obj.matrix_world @ v.co
        for smallObj in smallObjects:
            if not smallObj.data.vertices:
                continue
            for sv in smallObj.data.vertices:
                smallWorldCoord = smallObj.matrix_world @ sv.co
                dist = (worldCoord - smallWorldCoord).length
                if bestDistance is None or dist < bestDistance:
                    bestDistance = dist
                    bestWorldCoord = worldCoord

    if bestWorldCoord is not None:
        bpy.context.scene.cursor.location = bestWorldCoord
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        print(f"The origin of '{obj.name}' has been moved to the closest vertex: {bestWorldCoord} (distance {bestDistance:.4f})")
    else:
        print(f"No suitable vertex found in '{obj.name}' to change the origin.")








# ============================
# FUNCTIONS FOR WINDOWS
# ============================

def mainWindows():
    curveName = "00_A_CARP_curve_"
    meshObj = convertCurveToMesh(curveName)
    if not meshObj:
        print("Could not convert curve to mesh for windows. Process canceled.")
        return

    parts = separateByLooseParts(meshObj)
    print(f"{len(parts)} segments obtained from the window mesh.")

    mergedByVertices = unifyAllObjectsNearby(parts, threshold=0.15)
    print(f"After merging by vertices, {len(mergedByVertices)} objects remain for windows.")

    for partObj in mergedByVertices:
        updateOriginToGeometricCenter(partObj)

    finalObjects = unifyObjectsByCenters(mergedByVertices, threshold=0.5)
    print(f"After merging by centers, {len(finalObjects)} objects remain for windows.")

    tripleSolids = []
    for partObj in finalObjects:
        solids = createTripleSolidsFromObject(
            partObj, baseHeight=0.9, midHeight=1.3, topHeight=0.5
        )
        tripleSolids.extend(solids)
    print(f"{len(tripleSolids)} solids (triple set) have been created from windows.")

    for solid in tripleSolids:
        recalcNormals(solid)
        applyCubeUVUnwrap(solid)


def getObjectCorners(obj):
    """
    Gets the 4 corner points (top-left, top-right, bottom-left, bottom-right)
    of the 2D projection of the object's bounding box vertices in world space.
    """
    coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    zs = [c.z for c in coords]

    minX, maxX = min(xs), max(xs)
    minY, maxY = min(ys), max(ys)
    baseZ = min(zs)

    topLeft = Vector((minX, maxY, baseZ))
    topRight = Vector((maxX, maxY, baseZ))
    bottomLeft = Vector((minX, minY, baseZ))
    bottomRight = Vector((maxX, minY, baseZ))
    return topLeft, topRight, bottomLeft, bottomRight


def createPrismFromCorners(corners, height, zOffset, namePrefix="PRISMA"):
    topLeft, topRight, bottomLeft, bottomRight = corners
    v0 = bottomLeft + Vector((0, 0, zOffset))
    v1 = bottomRight + Vector((0, 0, zOffset))
    v2 = topRight + Vector((0, 0, zOffset))
    v3 = topLeft + Vector((0, 0, zOffset))
    v4 = v0 + Vector((0, 0, height))
    v5 = v1 + Vector((0, 0, height))
    v6 = v2 + Vector((0, 0, height))
    v7 = v3 + Vector((0, 0, height))
    verts = [v0, v1, v2, v3, v4, v5, v6, v7]
    faces = [
        [0, 1, 2, 3],  # bottom face
        [4, 5, 6, 7],  # top face
        [0, 1, 5, 4],
        [1, 2, 6, 5],
        [2, 3, 7, 6],
        [3, 0, 4, 7]
    ]
    mesh = bpy.data.meshes.new(namePrefix + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    objPrism = bpy.data.objects.new(namePrefix, mesh)
    bpy.context.collection.objects.link(objPrism)
    print(f"The prism '{namePrefix}' has been created with height {height} and offset {zOffset}.")
    return objPrism


def createThinPrismFromCorners(corners, height, zOffset, ratio=1/6, namePrefix="PRISMA_FINO"):
    """
    Creates a thin prism by reducing the Y dimension to 'ratio' of the original,
    extruding 'height' units in Z and applying a zOffset.
    """
    topLeft, topRight, bottomLeft, bottomRight = corners
    minX = bottomLeft.x
    maxX = topRight.x
    ys = [p.y for p in [topLeft, topRight, bottomLeft, bottomRight]]
    minY, maxY = min(ys), max(ys)
    baseZ = bottomLeft.z
    originalThickness = maxY - minY
    newThickness = originalThickness * ratio
    centerY = (minY + maxY) / 2

    newBottomLeft = Vector((minX, centerY - newThickness/2, baseZ))
    newBottomRight = Vector((maxX, centerY - newThickness/2, baseZ))
    newTopRight = Vector((maxX, centerY + newThickness/2, baseZ))
    newTopLeft = Vector((minX, centerY + newThickness/2, baseZ))

    v0 = newBottomLeft + Vector((0, 0, zOffset))
    v1 = newBottomRight + Vector((0, 0, zOffset))
    v2 = newTopRight + Vector((0, 0, zOffset))
    v3 = newTopLeft + Vector((0, 0, zOffset))
    v4 = v0 + Vector((0, 0, height))
    v5 = v1 + Vector((0, 0, height))
    v6 = v2 + Vector((0, 0, height))
    v7 = v3 + Vector((0, 0, height))
    verts = [v0, v1, v2, v3, v4, v5, v6, v7]
    faces = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [1, 2, 6, 5],
        [2, 3, 7, 6],
        [3, 0, 4, 7]
    ]
    mesh = bpy.data.meshes.new(namePrefix + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    objPrism = bpy.data.objects.new(namePrefix, mesh)
    bpy.context.collection.objects.link(objPrism)
    print(f"The thin prism '{namePrefix}' has been created with height {height} and offset {zOffset}.")
    return objPrism


def createTripleSolidsFromObject(obj, baseHeight=1.0, midHeight=0.7, topHeight=1.0):
    """
    Creates three solids from the bounding box of the object:
      - Base: prism of height baseHeight.
      - Middle: thin prism of height midHeight with offset baseHeight.
      - Top: prism of height topHeight with offset baseHeight + midHeight.
    """
    corners = getObjectCorners(obj)
    baseSolid = createPrismFromCorners(corners, height=baseHeight, zOffset=0, namePrefix="PRISMA_BASE_" + obj.name)
    midSolid = createThinPrismFromCorners(corners, height=midHeight, zOffset=baseHeight, namePrefix="PRISMA_MEDIO_" + obj.name)
    topSolid = createPrismFromCorners(corners, height=topHeight, zOffset=baseHeight + midHeight, namePrefix="PRISMA_TOP_" + obj.name)
    return [baseSolid, midSolid, topSolid]


def unifyObjectsByVertices(objects, threshold=0.15):
    vertexCoords = {obj: [obj.matrix_world @ v.co for v in obj.data.vertices] for obj in objects}
    groups = []
    for obj in objects:
        added = False
        for group in groups:
            if any((vc - voc).length < threshold for vc in vertexCoords[obj] for voc in vertexCoords[group[0]]):
                group.append(obj)
                added = True
                break
        if not added:
            groups.append([obj])

    mergedObjects = []
    for group in groups:
        if len(group) > 1:
            bpy.ops.object.select_all(action='DESELECT')
            for o in group:
                o.select_set(True)
            bpy.context.view_layer.objects.active = group[0]
            bpy.ops.object.join()
            joinedObj = bpy.context.view_layer.objects.active
            mergedObjects.append(joinedObj)
            print(f"Se unieron {len(group)} objetos en '{joinedObj.name}'.")
        else:
            mergedObjects.append(group[0])
    return mergedObjects


def unifyAllObjectsNearby(objects, threshold=0.15):
    prevCount = len(objects)
    while True:
        newObjects = unifyObjectsByVertices(objects, threshold)
        newCount = len(newObjects)
        if newCount == prevCount:
            break
        prevCount = newCount
        objects = newObjects
    return objects


def updateOriginToGeometricCenter(obj):
    if not obj:
        return
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    print(f"The origin of '{obj.name}' has been updated to its geometric center.")


def unifyObjectsByCenters(objects, threshold=0.5):
    centers = {obj: obj.location.copy() for obj in objects}
    groups = []
    for obj in objects:
        added = False
        for group in groups:
            if any((centers[obj] - centers[other]).length < threshold for other in group):
                group.append(obj)
                added = True
                break
        if not added:
            groups.append([obj])

    mergedObjects = []
    for group in groups:
        if len(group) > 1:
            bpy.ops.object.select_all(action='DESELECT')
            for o in group:
                o.select_set(True)
            bpy.context.view_layer.objects.active = group[0]
            bpy.ops.object.join()
            joinedObj = bpy.context.view_layer.objects.active
            print(f"{len(group)} objects were joined by centers into '{joinedObj.name}'.")
            mergedObjects.append(joinedObj)
        else:
            mergedObjects.append(group[0])
    return mergedObjects








# ============================
# FUNCTIONS FOR FURNITURE
# ============================

def mainFurniture():
    """
    Converts the object 'MesaRectangular_E30' to mesh, replaces its geometry
    with the 4 real extreme points, centers the origin, and rotates the object
    based on the orientation encoded in its name.
    """
    orientation_parts = separate_orientations()
    midpoints_world = convert_lines_to_midpoint_points(orientation_parts)
    for curveObj in list(bpy.data.objects):
        if curveObj.type == 'CURVE' and not curveObj.name.startswith("00_"):
            print(f"\nProcessing '{curveObj.name}'...")

            # Convert to mesh
            bpy.context.view_layer.objects.active = curveObj
            bpy.ops.object.select_all(action='DESELECT')
            curveObj.select_set(True)
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            points = getExtremePoints(curveObj)

            # Replace geometry
            meshData = curveObj.data
            meshData.clear_geometry()
            meshData.from_pydata(points, [], [])
            meshData.update()

            # Center the origin
            bpy.context.view_layer.objects.active = curveObj
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

            # Read direction and rotation from name
            rotationZ = computeOrientationAngleFromMidpoints(curveObj, midpoints_world)

            # Save original rotation
            originalRotation = curveObj.rotation_euler.copy()

            # Apply rotation
            curveObj.rotation_euler = Euler((0, 0, radians(rotationZ)), 'XYZ')
            bpy.context.view_layer.update()

            # Calculate length (Y) and width (X) after rotation
            bboxCoords = [curveObj.matrix_world @ v.co for v in curveObj.data.vertices]
            xCoords = [v.x for v in bboxCoords]
            yCoords = [v.y for v in bboxCoords]

            width = round(max(xCoords) - min(xCoords), 3)
            length = round(max(yCoords) - min(yCoords), 3)

            print(f"Dimensions: length (Y) = {length}, width (X) = {width}")

            # Rename object adding dimensions
            curveObj.name = f"{curveObj.name}_{length}L_{width}W_{rotationZ}R"
            print(f"Final object name: {curveObj.name}")

            # Restore original rotation
            curveObj.rotation_euler = originalRotation
            bpy.context.view_layer.update()
            print(f"Rotation restored to original.\n")


def separate_orientations():
    """
    Looks for the object "00_Orientacion_curve_", converts it to mesh,
    separates its pieces by loose parts, and returns the resulting object list.
    """
    name_target = "00_Orientacion_curve_"
    obj = bpy.data.objects.get(name_target)
    if obj is None:
        print(f"Object '{name_target}' not found.")
        return []

    # 1) Convert to mesh
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    # After conversion, 'obj' is now of type MESH.

    # 2) Before separating, store the existing object set
    before_objs = set(bpy.data.objects)

    # 3) Separate by loose parts
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 4) Detect the new objects created by the separation
    after_objs = set(bpy.data.objects)
    new_objs = list(after_objs - before_objs)

    # 5) The original object ('obj') is modified to contain
    #    one of the parts; the others are in new_objs.
    #    Return the full list of sub-objects:
    parts = [obj] + new_objs
    print(f"Separation complete: {len(parts)} sub-objects generated.")
    for p in parts:
        print(f"  • {p.name}")

    return parts


def convert_lines_to_midpoint_points(orientation_parts):
    """
    For each object in orientation_parts (each one a mesh with one or more segments):
      - For each edge in the mesh:
          • Computes the midpoint in global coordinates.
          • Computes the slope between the two vertices of the edge.
          • Creates a new point-object at that position, renaming it to include
            the midpoint coordinates and the slope.
      - Deletes the original object (which contained all the segments).
    Returns:
      - A list of tuples (midpoint, slope), where:
          • midpoint is a mathutils.Vector with the global coordinates of the midpoint.
          • slope is the slope (float) of the segment. For vertical lines, slope = float('inf').
    """
    midpoint_info = []

    for part in orientation_parts:
        mesh = part.data
        verts = mesh.vertices
        edges = mesh.edges

        # If there are no edges, skip this object
        if len(edges) == 0:
            continue

        for i, edge in enumerate(edges):
            idx0, idx1 = edge.vertices
            co0 = verts[idx0].co
            co1 = verts[idx1].co

            # Convert to global coordinates
            wv0 = part.matrix_world @ co0
            wv1 = part.matrix_world @ co1

            # Compute midpoint in world space
            midpoint = (wv0 + wv1) / 2.0

            # Compute slope: (y1 - y0) / (x1 - x0), handling vertical lines
            dx = wv1.x - wv0.x
            dy = wv1.y - wv0.y
            if abs(dx) < 1e-6:
                slope = float('inf')
            else:
                slope = dy / dx

            midpoint_info.append((midpoint, slope))

            # Create a new mesh (a single vertex at local origin)
            mesh_name = f"{part.name}_seg{i}_mesh"
            point_mesh = bpy.data.meshes.new(mesh_name)
            point_mesh.from_pydata([(0.0, 0.0, 0.0)], [], [])
            point_mesh.update()

            # Create object for that mesh-point
            # Format coordinates and slope to 2 decimal places
            x_str = f"{midpoint.x:.2f}"
            y_str = f"{midpoint.y:.2f}"
            if slope == float('inf'):
                slope_str = "90"
            else:
                slope_str = f"{slope:.2f}"

            obj_name = (
                f"{part.name}_seg{i}_pt_"
                f"({x_str},{y_str})_slope_{slope_str}"
            )
            # Replace invalid characters for object name
            obj_name = obj_name.replace(" ", "").replace("(", "").replace(")", "").replace(",", "_")

            point_obj = bpy.data.objects.new(obj_name, point_mesh)
            bpy.context.collection.objects.link(point_obj)

            # Set the object location to the midpoint
            point_obj.location = midpoint

        # Delete the original object after processing all its edges
        bpy.data.objects.remove(part, do_unlink=True)

    print(f"Converted segments into {len(midpoint_info)} midpoint points with slope.")
    return midpoint_info


def computeOrientationAngleFromMidpoints(curveObj, midpoints_world):
    """
    Returns an angle in [0,360) based on the direction from the
    origin of `curveObj` to the closest midpoint in midpoints_world.
    - curveObj: object whose rotation we want to compute (its origin is already centered).
    - midpoints_world: list of Vector3 in world space.
    """
    # Position of the origin of curveObj in world space
    origin_world = curveObj.matrix_world.translation

    best_angle = 0.0
    best_dist_sq = float('inf')

    for midpoint,_ in midpoints_world:
        vec = midpoint - origin_world
        dist_sq = vec.length_squared
        angle = (degrees(atan2(vec.y, vec.x)) + 360.0) % 360.0

        if dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            best_angle = angle

    return round(best_angle, 2)








# ============================
# FUNCTIONS FOR FLOOR AND CEILING
# ============================
def createFloorFromCorners(corners, depth=1.0, z_offset=0.0, namePrefix="PRISM"):
    """
    Creates a prism from 4 points (Vector) in the order returned by getExtremePoints,
    with a height `depth` and offset `z_offset` units in Z.
    - corners: list of 4 mathutils.Vector, consistently ordered.
    - depth: thickness of the prism along the base normal.
    - z_offset: vertical offset applied to all geometry before creation.
    """
    # Apply Z offset to base vertices
    base_verts = [Vector((v.x, v.y, v.z + z_offset)) for v in corners]

    # Calculate the base normal
    v0, v1, v2, _ = base_verts
    normal = (v1 - v0).cross(v2 - v0).normalized()

    # Generate top face vertices by extruding along the normal
    top_verts = [v + normal * depth for v in base_verts]

    # All vertices of the prism: base + top
    verts = base_verts + top_verts

    # Faces: base, top, and 4 lateral faces
    faces = [
        [0, 1, 2, 3],       # base
        [4, 5, 6, 7],       # top
        [0, 1, 5, 4],       # side 1
        [1, 2, 6, 5],       # side 2
        [2, 3, 7, 6],       # side 3
        [3, 0, 4, 7],       # side 4
    ]

    mesh = bpy.data.meshes.new(namePrefix + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(namePrefix, mesh)
    bpy.context.collection.objects.link(obj)
    print(f"'{obj.name}' has been created (depth={depth}, z_offset={z_offset}).")
    return obj


def mainSurface():
    """
    Selects curves, gets their 4 corners, and creates two prism-planes:
      1) with thickness 0.1, offset -0.1 in Z
      2) with thickness 0.1, offset +2.8 in Z
    """
    prefix = "00_A_MUROS"
    curves = [o for o in bpy.data.objects if o.type == 'CURVE' and o.name.startswith(prefix)]
    if not curves:
        print(f"No curves found with prefix '{prefix}'.")
        return

    for curve in curves:
        meshObj = convertCurveToMesh(curve.name)
        if not meshObj:
            continue

        corners = getExtremePoints(meshObj)
        base_name = meshObj.name

        # Lower floor: thickness 0.1, 0.1 lower
        floor = createFloorFromCorners(corners,
                               depth=0.1,
                               z_offset=-0.1,
                               namePrefix=f"FLOOR_LOWER_{base_name}")
        recalcNormals(floor)
        applyCubeUVUnwrap(floor)

        # Upper floor: thickness 0.1, at height 2.8
        ceiling = createFloorFromCorners(corners,
                               depth=0.1,
                               z_offset=2.7,
                               namePrefix=f"FLOOR_UPPER_{base_name}")
        recalcNormals(ceiling)
        applyCubeUVUnwrap(ceiling)








# ============================
# FUNCTIONS FOR LIGHTS
# ============================
def mainLights():
    curveName = "00_Iluminacion_curve_"
    meshObj = convertCurveToMesh(curveName)
    if not meshObj:
        print(f"Could not convert '{curveName}' to mesh. Light processing canceled.")
        return

    parts = separateByLooseParts(meshObj)
    print(f"{len(parts)} light points detected.")

    for i, obj in enumerate(sorted(parts, key=lambda o: o.name)):
        newName = f"Luz" if i == 0 else f"Luz.{i:03d}"
        print(f"Renaming '{obj.name}' to '{newName}'")
        obj.name = newName
        updateOriginToGeometricCenter(obj)








# ============================
# MAIN
# ============================

def mainScript(savePath):
    parseNames()
    mainSurface()
    mainFurniture()
    mainWalls()
    mainDoors()
    mainWindows()
    mainLights()
    saveBlend(savePath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to generate walls, doors and windows in Blender"
    )
    parser.add_argument(
        "--base-path",
        required=True,
        dest="savePath",
        help="Base path of your project (where the blender/ folder is located)"
    )
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    mainScript(args.savePath)
