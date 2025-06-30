using UnityEngine;

public class SwitchModel : MonoBehaviour
{
    private GameObject originalFloor;
    private GameObject reformedFloor;
    private bool reform = false;

    public void FindInstances()
    {
        originalFloor = GameObject.Find("original_Instance");
        reformedFloor = GameObject.Find("reformed_Instance");
        reformedFloor.SetActive(false);

        if (originalFloor == null || reformedFloor == null)
            Debug.LogError("[SwitchModel] One or both floor instances not found by name.");
    }

    public void SwitchModelState()
    {
        if (originalFloor == null || reformedFloor == null)
        {
            Debug.LogWarning("[SwitchModel] Cannot switch: objects not found.");
            return;
        }

        reform = !reform;

        originalFloor.SetActive(!reform);
        reformedFloor.SetActive(reform);
    }
}
