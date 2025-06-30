using UnityEngine;

public static class LightPlacer
{
    private const string LampPrefabPath = "Furniture/BA_Ceiling Light_01";

    public static GameObject PlaceLight(Transform tr)
    {
        if (tr == null)
        {
            Debug.LogError("[LightPlacer] Null transform received");
            return null;
        }

        // 1) Load the lamp prefab
        GameObject prefab = Resources.Load<GameObject>(LampPrefabPath);
        if (prefab == null)
        {
            Debug.LogError($"[LightPlacer] Prefab not found at Resources/{LampPrefabPath}");
            return null;
        }

        // 2) Compute spawn position: use X and Z from marker, and fixed Y=2.7
        Vector3 spawnPos = new Vector3(
            tr.position.x,
            2.7f,
            tr.position.z
        );

        // 3) Instantiate under the same parent as the marker
        GameObject instance = GameObject.Instantiate(
            prefab,
            spawnPos,
            Quaternion.identity,
            tr.parent
        );

        Debug.Log($"[LightPlacer] Ceiling lamp instantiated at {instance.transform.position}");

        // 4) Deactivate the marker object
        tr.gameObject.SetActive(false);

        return instance;
    }
}
