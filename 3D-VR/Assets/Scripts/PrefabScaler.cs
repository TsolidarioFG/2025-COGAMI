// PrefabScaler.cs
using System;
using System.Linq;
using System.Text.RegularExpressions;
using UnityEngine;
using System.Globalization;
using System.Collections.Generic;

public static class PrefabScaler
{
    // Contains prefab path, original size (x: width, y: depth), and Thin flag
    private class FurnitureInfo
    {
        public string PrefabPath;
        public Vector2 OriginalSize;
    }

    private static readonly Dictionary<string, FurnitureInfo> FurnitureConfigs =
        new Dictionary<string, FurnitureInfo>(StringComparer.OrdinalIgnoreCase)
    {
        { "CamaIndividual", new FurnitureInfo {
            PrefabPath     = "Furniture/CamaIndividual",
            OriginalSize   = new Vector2(3.257153f, 1.571005f)
            }
        },
        { "CamaMatrimonio", new FurnitureInfo {
            PrefabPath     = "Furniture/CamaMatrimonio",
            OriginalSize   = new Vector2(3.799233f, 3.148135f)
            }
        },
        { "Lavabo", new FurnitureInfo {
            PrefabPath     = "Furniture/Lavabo",
            OriginalSize   = new Vector2(0.7146341f, 1.35088f)
            }
        },
        { "Inodoro", new FurnitureInfo {
            PrefabPath     = "Furniture/Inodoro",
            OriginalSize   = new Vector2(1.188786f, 0.6891798f)
            }
        },
        { "Ducha", new FurnitureInfo {
            PrefabPath     = "Furniture/Ducha",
            OriginalSize   = new Vector2(1.836204f, 1.836204f)
            }
        },
        { "Encimera", new FurnitureInfo {
            PrefabPath     = "Furniture/Encimera",
            OriginalSize   = new Vector2(0.992867f, 1.16401f)
            }
        },
        { "Fregadero", new FurnitureInfo {
            PrefabPath     = "Furniture/Fregadero",
            OriginalSize   = new Vector2(0.907429f, 1.361143f)
            }
        },
        { "FregaderoAbierto", new FurnitureInfo {
            PrefabPath     = "Furniture/FregaderoAbierto",
            OriginalSize   = new Vector2(0.907429f, 1.361143f)
            }
        },
        { "Nevera", new FurnitureInfo {
            PrefabPath     = "Furniture/Nevera",
            OriginalSize   = new Vector2(0.9164716f, 1.092634f)
            }
        },
        { "Fuegos", new FurnitureInfo {
            PrefabPath     = "Furniture/Fuegos",
            OriginalSize   = new Vector2(0.8933326f, 1.111728f)
            }
        },
        { "FuegosAbierto", new FurnitureInfo {
            PrefabPath     = "Furniture/FuegosAbierto",
            OriginalSize   = new Vector2(0.8933326f, 1.111728f)
            }
        },
        { "Mesilla", new FurnitureInfo {
            PrefabPath     = "Furniture/Mesilla",
            OriginalSize   = new Vector2(0.6353572f, 0.6341963f)
            }
        },
        { "Almacenamineto", new FurnitureInfo {
            PrefabPath     = "Furniture/Almacenamiento",
            OriginalSize   = new Vector2(0.8180385f, 1.07484f)
            }
        },
        { "MesaRedonda", new FurnitureInfo {
            PrefabPath     = "Furniture/MesaRedonda",
            OriginalSize   = new Vector2(2.225178f, 2.225178f)
            }
        },
        { "MesaRectangular", new FurnitureInfo {
            PrefabPath     = "Furniture/MesaRectangular",
            OriginalSize   = new Vector2(1.314353f, 2.074194f)
            }
        },
        { "Bide", new FurnitureInfo {
            PrefabPath     = "Furniture/Bide/Bide",
            OriginalSize   = new Vector2(0.5397641f, 0.3574774f)
            }
        },
        { "SofaDerecha", new FurnitureInfo {
            PrefabPath     = "Furniture/SofaIzquierda",
            OriginalSize   = new Vector2(0.9287868f, 0.9556539f)
            }
        },
        { "SofaIzquierda", new FurnitureInfo {
            PrefabPath     = "Furniture/SofaDerecha",
            OriginalSize   = new Vector2(0.9287868f, 0.9556539f)
            }
        },
        { "SofaIntermedio", new FurnitureInfo {
            PrefabPath     = "Furniture/SofaIntermedio",
            OriginalSize   = new Vector2(0.9739578f, 0.938403f)
            }
        },
        { "SofaEsquina", new FurnitureInfo {
            PrefabPath     = "Furniture/SofaEsquina",
            OriginalSize   = new Vector2(0.9461575f, 0.9527255f)
            }
        },
        { "Armario", new FurnitureInfo {
            PrefabPath     = "Furniture/Armario",
            OriginalSize   = new Vector2(0.5052456f, 1.8f)
            }
        },
        { "Lavadora", new FurnitureInfo {
            PrefabPath     = "Furniture/Lavadora",
            OriginalSize   = new Vector2(0.6144176f, 0.7034974f)
            }
        }
    };

    public static void InstantiateFurniture(Transform placeholder)
    {
        string name = placeholder.name;

        // Look for the config whose key appears in the name
        var kv = FurnitureConfigs
            .FirstOrDefault(x => name.IndexOf(x.Key, StringComparison.OrdinalIgnoreCase) >= 0);

        if (kv.Equals(default(KeyValuePair<string, FurnitureInfo>)))
        {
            Debug.LogWarning($"[PrefabScaler] No configuration found for '{name}'.");
            return;
        }

        var config = kv.Value;
        var prefab = Resources.Load<GameObject>(config.PrefabPath);
        if (prefab == null)
        {
            Debug.LogError($"[PrefabScaler] Prefab not found: Resources/{config.PrefabPath}");
            return;
        }

        // Instantiate at the placeholder's position
        var instance = GameObject.Instantiate(
            prefab,
            placeholder.position,
            Quaternion.identity,
            placeholder.parent
        );
        instance.name = prefab.name + "_Instance";

        // Apply rotation and scale
        ApplyRotationFromName(instance.transform, name);
        ApplyScale(instance.transform, name, config.OriginalSize);

        Debug.Log($"[PrefabScaler] Instantiated '{instance.name}' for '{name}'.");
        placeholder.gameObject.SetActive(false);
    }

    public static void ApplyRotationFromName(Transform t, string name)
    {
        // Look for a suffix ending in 'R': decimal number before the 'R'
        var m = Regex.Match(name, @"(\d+(\.\d+)?)R$", RegexOptions.IgnoreCase);
        if (m.Success)
        {
            float angle = float.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
            t.localEulerAngles = new Vector3(0f, -(angle % 360f), 0f);
            Debug.Log($"[PrefabScaler] Rotated {angle}° from '_xxxR' suffix in '{t.name}'.");
        }
        else
        {
            Debug.LogWarning($"[PrefabScaler] No angle with 'R' found in name: '{t.name}'.");
        }
    }

    private static void ApplyScale(Transform t, string name, Vector2 originalSize)
    {
        var m = Regex.Match(name, @"_(\d+(\.\d+)?)L_(\d+(\.\d+)?)A", RegexOptions.IgnoreCase);
        float length, width;

        if (m.Success)
        {
            length = float.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
            width  = float.Parse(m.Groups[3].Value, CultureInfo.InvariantCulture);

            var s = t.localScale;
            s.x = width / originalSize.x;
            s.z = length / originalSize.y;
            t.localScale = s;

            Debug.Log($"[PrefabScaler] '{name}': min={width:F2}, max={length:F2}, scale.z={s.z:F3}, originalSizeX={originalSize.x}, originalSizeY={originalSize.y}");
        }
    }
}
