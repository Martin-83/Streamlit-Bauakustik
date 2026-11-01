import math

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# Gültigkeitsbereich der Kurven (SIA 181, Figur 11) in kg/m2
M_MIN = 4.0
M_MAX = {"Massiv": 500.0, "Holz": 65.0, "Glas": 100.0, "Blech": 200.0}

# Kurven 1 und 2: oberhalb ihrer Formelgrenze verläuft R'w waagrecht weiter,
# bis zum Ende der Figur (aus Figur 11 abgelesen, bei Bedarf hier anpassen).
PLATEAU = ("Massiv", "Blech")
R_PLATEAU = 57.0
M_FIGUR_ENDE = 800.0

FARBEN = {"Massiv": "#1f3b73", "Holz": "#2e8b57", "Glas": "#d9822b", "Blech": "#c0392b"}
TICKS = [2, 3.1, 5, 8, 12.5, 20, 31, 50, 80, 125, 200, 315, 500, 800]


def schalldaemmung(material, M):
    if material == "Massiv":     # Kurve 2 (Gösele)
        r = -15 + 118*M - 119*M**2 + 50.6*M**3 - 7.06*M**4
    elif material == "Holz":     # Kurve 3 (Lauber)
        r = -2.8 + 105*M - 155*M**2 + 98.7*M**3 - 21*M**4
    elif material == "Glas":     # Kurve 4 (Lauber)
        r = 9.2 + 30*M - 6.2*M**2 - 7.6*M**3 + 3.3*M**4
    else:                        # Blech: Kurve 1 (Massengesetz)
        r = 20*M + 11
    if material in PLATEAU:
        r = np.minimum(r, R_PLATEAU)
    return r


# Obergrenze der Anwendung: bei Kurven mit Plateau das Ende der Figur
M_OBEN = {name: (M_FIGUR_ENDE if name in PLATEAU else m) for name, m in M_MAX.items()}

st.title("Luftschalldämmung nach SIA 181")

material = st.radio("Material", list(M_MAX), horizontal=True)
staerke = st.number_input("Stärke (mm)", value=200.0, step=10.0, format="%.1f")
rohdichte = st.number_input("Rohdichte (kg/m³)", value=2400.0, step=100.0, format="%.0f")

masse = staerke / 1000 * rohdichte
st.metric("Flächenbezogene Masse", f"{masse:.1f} kg/m²")

im_bereich = M_MIN - 1e-6 <= masse <= M_OBEN[material] + 1e-6
if im_bereich:
    rw = float(schalldaemmung(material, math.log10(masse)))
    st.metric("R'w", f"{rw:.1f} dB")
    if masse > M_MAX[material]:
        st.info(
            f"Oberhalb von {M_MAX[material]:g} kg/m² steigt R'w nicht mehr an, "
            f"es gilt das Plateau von {R_PLATEAU:g} dB (Figur 11)."
        )
else:
    st.warning(
        f"Die Masse liegt ausserhalb des gültigen Bereichs für {material} "
        f"({M_MIN:g}–{M_OBEN[material]:g} kg/m²). R'w wird nicht berechnet."
    )

# --- Diagramm ---
plt.rcParams.update({"font.size": 13, "axes.edgecolor": "0.6"})
fig, ax = plt.subplots(figsize=(8, 5.4), dpi=200)

# Beschriftung am Kurvenende; bei Kurven mit Plateau stattdessen auf der Waagrechten
LABEL = {
    "Massiv": ((520, R_PLATEAU), (0, 10), "center"),
    "Blech": ((250, R_PLATEAU), (0, 10), "center"),
}

for name, m_max in M_MAX.items():
    gewaehlt = name == material
    stil = dict(color=FARBEN[name], lw=3.5 if gewaehlt else 1.8,
                alpha=1.0 if gewaehlt else 0.5, solid_capstyle="round")

    # Bereich der Formel: durchgezogen
    m = np.logspace(np.log10(M_MIN), np.log10(m_max), 300)
    r = schalldaemmung(name, np.log10(m))
    ax.plot(m, r, **stil)

    # Plateau: gestrichelt bis zum Ende der Figur
    if name in PLATEAU:
        m2 = np.logspace(np.log10(m_max), np.log10(M_FIGUR_ENDE), 100)
        ax.plot(m2, schalldaemmung(name, np.log10(m2)), ls="--", **stil)

    xy, versatz, ha = LABEL.get(name, ((m[-1], r[-1]), (8, 0), "left"))
    ax.annotate(name, xy, textcoords="offset points", xytext=versatz,
                va="center", ha=ha, color=FARBEN[name], fontsize=13,
                fontweight="bold" if gewaehlt else "normal",
                alpha=1.0 if gewaehlt else 0.7)

if im_bereich:
    # gestrichelte Hilfslinien zu den Achsen
    ax.plot([masse, masse], [15, rw], color="0.3", lw=1, ls=":", zorder=4)
    ax.plot([2, masse], [rw, rw], color="0.3", lw=1, ls=":", zorder=4)
    ax.plot(masse, rw, "o", color=FARBEN[material], ms=13, mec="white", mew=2.5, zorder=5)
    # bei sehr grossen Massen Box nach links, damit sie nicht über den Rand ragt
    gross = masse > 600
    ax.annotate(f"{rw:.1f} dB", (masse, rw), textcoords="offset points",
                xytext=(14, -38) if gross else (0, -38),
                ha="right" if gross else "center",
                fontsize=15, fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=FARBEN[material]))

ax.set_xscale("log")
ax.set_xlim(2, 800)
ax.set_ylim(15, 65)
ax.set_xticks(TICKS)
ax.set_xticklabels([f"{t:g}" for t in TICKS], rotation=45, ha="right", fontsize=11)
ax.set_yticks(range(15, 66, 5))
ax.minorticks_off()
ax.grid(True, color="0.9", lw=1)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(length=0)
ax.set_xlabel("Flächenbezogene Masse m′ (kg/m²)")
ax.set_ylabel("R′w (dB)")
fig.tight_layout()

st.pyplot(fig)