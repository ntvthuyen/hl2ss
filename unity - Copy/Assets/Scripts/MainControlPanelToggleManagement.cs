using Microsoft.MixedReality.Toolkit.UI;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MainControlPanelToggleManagement : MonoBehaviour
{
    public List<GameObject> toggles;
    // Start is called before the first frame update
    void Start()
    {

    }

    // Update is called once per frame
    void Update()
    {


    }
    public int GetToggleIndex()
    {

        foreach (GameObject go in toggles)
        {
            if (go.GetComponent<Interactable>().IsToggled) return toggles.IndexOf(go);
        }
        return -1;
    }
    public void UnToggleAllExcept(int index)
    {
        Debug.Log("untoggle except" + index.ToString());

        for (int i = 0; i < toggles.Count; ++i)
        {
            if (i == index) continue;
            toggles[i].GetComponent<Interactable>().IsToggled = false;
        }
    }

   
}
