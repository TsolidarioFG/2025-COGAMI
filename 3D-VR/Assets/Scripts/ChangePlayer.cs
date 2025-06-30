using UnityEngine;

public class ChangePlayer : MonoBehaviour
{
    [Header("Referencias")]
    public GameObject wheelChair;
    public CapsuleCollider capsuleCollider;
    public GameObject cameraObject; // ← nueva referencia

    [Header("Height and center - Standing Mode")]
    public float standingHeight = 1.75f;
    public Vector3 standingCenter = new Vector3(0, 0.875f, 0);
    public float standingCameraY = 1.6f;

    [Header("Height and center - Seated Mode")]
    public float seatedHeight = 1.2f;
    public Vector3 seatedCenter = new Vector3(0, 0.6f, 0);
    public float seatedCameraY = 1.1f;

    public void SwitchToPlayer()
    {
        if (capsuleCollider != null)
        {
            capsuleCollider.height = standingHeight;
            capsuleCollider.center = standingCenter;
        }

        if (cameraObject != null)
        {
            Vector3 camPos = cameraObject.transform.localPosition;
            cameraObject.transform.localPosition = new Vector3(camPos.x, standingCameraY, camPos.z);
        }

        if (wheelChair != null)
        {
            wheelChair.SetActive(false);
        }
    }

    public void SwitchToSeated()
    {
        if (capsuleCollider != null)
        {
            capsuleCollider.height = seatedHeight;
            capsuleCollider.center = seatedCenter;
        }

        if (cameraObject != null)
        {
            Vector3 camPos = cameraObject.transform.localPosition;
            cameraObject.transform.localPosition = new Vector3(camPos.x, seatedCameraY, camPos.z);
        }

        if (wheelChair != null)
        {
            wheelChair.SetActive(true);
        }
    }
}
