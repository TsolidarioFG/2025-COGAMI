using System.Collections.Generic;
using UnityEngine;
using Unity.VRTemplate;

[DisallowMultipleComponent]
public class GenerateModel : MonoBehaviour
{
    #region Inspector

    [Header("Prefab (Resources)")]
    [Tooltip("Path inside Resources to the prefab that contains walls, doors and windows.")]
    private string prefabPath1 = "original";
    private string prefabPath2 = "reformed";

    [Header("Name Prefixes")]
    private string wallPrefix = "00_A_MUROS";
    private string doorPrefix = "PUERTA";
    private string doorBorderPrefix = "00_A_PUERTA";
    private string windowPrefix = "PRISMA_MEDIO_00_A_CARP";
    private string windowTopPrefix = "PRISMA_TOP_00_A_CARP";
    private string windowBasePrefix = "PRISMA_BASE_00_A_CARP";
    private string floorPrefix = "FLOOR_LOWER";
    private string ceilingPrefix = "FLOOR_UPPER";
    private string lightPrefix = "Luz";

    [Header("Materials (Resources/Materials)")]
    private string wallMatPath = "Materials/BaseWall";
    private string doorMatPath = "Materials/BrownWood";
    private string doorBorderMatPath = "Materials/DarkWood";
    private string windowMatPath = "Materials/Window";
    private string floorMatPath = "Materials/WoodFloor";
    private string ceilingMatPath = "Materials/Concrete";
    private string hoverMatPath = "Materials/OnHover";

    [Header("XRKnob Parameters")]
    [SerializeField, Tooltip("Door rotation sensitivity")]
    private float knobSensitivity = 0.001f;

    private bool _isLoaded = false;

    #endregion

    private readonly Dictionary<string, Material> _materialCache = new();

    public void LoadFloor()
    {
        if (_isLoaded)
        {
            Debug.LogWarning("[FloorLoader] Floor already loaded.");
            return;
        }

        LoadModel(false);
        LoadModel(true);
        InitializeSwitchModel();
    }

    private void InitializeSwitchModel()
    {
        var switchModel = FindObjectOfType<SwitchModel>();
        if (switchModel != null)
        {
            switchModel.FindInstances();
            Debug.Log("[GenerateModel] SwitchModel initialized correctly.");
        }
        else
        {
            Debug.LogError("[GenerateModel] No SwitchModel component found in the scene.");
        }
    }

    private void LoadModel(bool reform)
    {
        if (!TryInstantiatePrefab(reform, out var root)) return;

        foreach (var tr in root.GetComponentsInChildren<Transform>(true))
        {
            string n = tr.name;

            if (n.StartsWith(wallPrefix))
            {
                EnsureCollider<MeshCollider>(tr.gameObject);
                AssignMaterial(tr, wallMatPath);
            }
            else if (n.StartsWith(doorPrefix))
            {
                EnsureCollider<BoxCollider>(tr.gameObject);
                AssignMaterial(tr, doorMatPath);
                ConfigureDoorRotation(tr);
            }
            else if (n.StartsWith(doorBorderPrefix))
            {
                EnsureCollider<MeshCollider>(tr.gameObject);
                AssignMaterial(tr, doorBorderMatPath);
            }
            else if (n.StartsWith(windowPrefix))
            {
                EnsureCollider<MeshCollider>(tr.gameObject);
                AssignMaterial(tr, windowMatPath);
            }
            else if (n.StartsWith(windowTopPrefix) || n.StartsWith(windowBasePrefix))
            {
                EnsureCollider<MeshCollider>(tr.gameObject);
                AssignMaterial(tr, wallMatPath);
            }
            else if (n.StartsWith(floorPrefix))
            {
                EnsureCollider<MeshCollider>(tr.gameObject);
                AssignMaterial(tr, floorMatPath);
                ConfigureTeleportationArea(tr.gameObject);
            }
            else if (n.StartsWith(ceilingPrefix))
            {
                EnsureCollider<MeshCollider>(tr.gameObject);
                AssignMaterial(tr, ceilingMatPath);
            }
            else if (n.StartsWith(lightPrefix))
            {
                LightPlacer.PlaceLight(tr);
            }
            else
            {
                PrefabScaler.InstantiateFurniture(tr);
            }
        }
    }

    #region Helper Methods

    private bool TryInstantiatePrefab(bool reform, out GameObject instance)
    {
        string pathToLoad = reform ? prefabPath2 : prefabPath1;
        if (string.IsNullOrEmpty(pathToLoad))
        {
            Debug.LogError("[FloorLoader] Prefab path is not set.");
            instance = null;
            return false;
        }

        var prefab = Resources.Load<GameObject>(pathToLoad);
        if (prefab == null)
        {
            Debug.LogError($"[FloorLoader] Prefab not found: Resources/{pathToLoad}");
            instance = null;
            return false;
        }

        if (reform)
        {
            _isLoaded = true;
        }

        instance = Instantiate(prefab, Vector3.zero, Quaternion.identity);
        instance.name = prefab.name + "_Instance";
        Debug.Log($"[FloorLoader] Prefab '{prefab.name}' instantiated at {Vector3.zero} (reform={reform}).");
        return true;
    }

    private void ConfigureDoorRotation(Transform door)
    {
        var go = door.gameObject;

        // 1) Add/configure HingeJoint (creates Rigidbody if needed)
        var hinge = go.AddComponent<HingeJoint>();
        hinge.anchor = Vector3.zero;           // Pivot point at local origin
        hinge.axis = Vector3.forward;          // Z-axis (0,0,1)

        var rb = go.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.linearDamping = 5f;
        }

        // 2) Add/configure XRGrabInteractable
        var grab = go.GetComponent<UnityEngine.XR.Interaction.Toolkit.Interactables.XRGrabInteractable>()
                ?? go.AddComponent<UnityEngine.XR.Interaction.Toolkit.Interactables.XRGrabInteractable>();
        grab.movementType = UnityEngine.XR.Interaction.Toolkit.Interactables.XRBaseInteractable.MovementType.VelocityTracking;
    }

    private void ConfigureTeleportationArea(GameObject go)
    {
        var tpArea = go.GetComponent<UnityEngine.XR.Interaction.Toolkit.Locomotion.Teleportation.TeleportationArea>();
        if (tpArea == null)
            tpArea = go.AddComponent<UnityEngine.XR.Interaction.Toolkit.Locomotion.Teleportation.TeleportationArea>();

        tpArea.selectMode = UnityEngine.XR.Interaction.Toolkit.Interactables.InteractableSelectMode.Multiple;
        tpArea.interactionLayers = UnityEngine.XR.Interaction.Toolkit.InteractionLayerMask.GetMask("Teleport");
    }

    private void AssignMaterial(Transform target, string matPath) =>
        SetMaterial(target, LoadMaterial(matPath));

    private void SetMaterial(Transform t, Material mat)
    {
        if (mat == null) return;
        if (t.TryGetComponent<MeshRenderer>(out var mr)) mr.material = mat;
    }

    private Material LoadMaterial(string path)
    {
        if (_materialCache.TryGetValue(path, out var cached)) return cached;
        var mat = Resources.Load<Material>(path);
        if (mat == null)
            Debug.LogWarning($"[FloorLoader] Material not found: Resources/{path}");
        else
            _materialCache[path] = mat;
        return mat;
    }

    private static T EnsureComponent<T>(GameObject go) where T : Component =>
        go.TryGetComponent(out T c) ? c : go.AddComponent<T>();

    private static void EnsureCollider<T>(GameObject go) where T : Collider
    {
        if (!go.TryGetComponent<T>(out _)) go.AddComponent<T>();
    }

    #endregion
}
