# 🐧 Perfil de Sistema & Filosofía Linux: Arquitecto Pragmático

---

## 🚀 1. Filosofía & Enfoque Técnico
* **Pragmatismo FOSS:** Priorizo la transparencia, la estabilidad y la libertad del software libre, pero mantengo los pies en la tierra. Si necesito drivers o herramientas propietarias para productividad o rendimiento, los integro sin dogmas.
* **Aprendizaje por Inmersión:** Veo las curvas de aprendizaje como una inversión. Asumir retos técnicos (como forzar el aprendizaje de Bash o Python) es mi método principal para dominar la arquitectura del sistema.
* **Curiosidad sobre Confort:** La elección de herramientas (Qtile, Wayland) no nace solo de preferencia estática, sino del deseo de probar límites personales. Comprender hasta que punto el sistema se amolda a mi y no yo a él
---

## 🛠️ 2. Stack Tecnológico

* **Distribución:** Debian Testing (El *sweet spot* entre la solidez `.deb` y paquetes/kernel actualizados).
* **Protocolo Gráfico:** Wayland (Transición desde la nostalgia de X11 hacia el estándar moderno).
* **Gestor de Ventanas (WM):** Qtile (`config.py`).


[ Debian Testing ] ──► [ Wayland ] ──► [ Qtile (Python) ]

---

## 📊 3. Matriz de Evaluación de Window Managers

| WM | Vistas / Evaluadas | Razonamiento & Dictamen |
| :--- | :--- | :--- |
| **Hyprland** | Vistoso y moderno. | *Descartado:* Demasiado complejo/cargado para empezar. |
| **Sway** | Estabilidad y heredero directo de i3. | *Descartado:* La configuración en un solo texto plano se vuelve caótica. |
| **BSPWM** | Modularidad impecable y división binaria. | *Contender:* Ideal para formalizar mi aprendizaje acelerado de Bash via IPC. |
| **Qtile** | **Elección Definitiva** | **Lienzo en blanco:** Permite programar mi propio entorno en Python puro. |

---

## 🎯 4. Meta del Proyecto Actual
* Desarrollar e integrar lógica personalizada (widgets, atajos y layouts) inspirada en las mejores características de otros WMs, construida directamente por mí en Python dentro de Qtile.
