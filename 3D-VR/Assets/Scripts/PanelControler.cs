using UnityEngine;

public class PanelControler : MonoBehaviour
{
    [Header("Panel References")]
    public GameObject buildPanel;
    public GameObject userPanel;
    public GameObject switchPanel;

    [Header("Panel States")]
    public bool buildPanelActive = false;
    public bool userPanelActive = false;
    public bool reform = false;

    // Llama a este método para alternar el estado del panel de construcción
    public void ToggleBuildPanel()
    {
        buildPanelActive = !buildPanelActive;
        userPanelActive = false;

        buildPanel.SetActive(buildPanelActive);
        userPanel.SetActive(false);
    }

    // Llama a este método para alternar el estado del panel de usuario
    public void ToggleUserPanel()
    {
        userPanelActive = !userPanelActive;
        buildPanelActive = false;

        userPanel.SetActive(userPanelActive);
        buildPanel.SetActive(false);
    }
}
