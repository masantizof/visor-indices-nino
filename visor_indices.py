import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Índices El Niño | UNGRD",
    layout="wide",
    page_icon="🌡️"
)

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
GEOJSON_PATH = os.path.join(RUTA_BASE, "DatosIndice_simple.geojson")

INDICES = {
    "Incendios Forestales":       "I_IF",
    "Inundaciones":               "I_Inundaci",
    "Vendavales":                 "I_Vendaval",
    "Movimientos en Masa":        "I_MovMasa",
    "Desabastecimiento de Agua":  "I_Desabast",
    "Daño Hidrológico – Lluvias": "I_DHTLL_In",
    "Daño Hidrológico – Sequía":  "I_DHTS_I_D",
    "Crecientes":                 "I_Crecient",
    "Avenidas Torrenciales":      "I_AVT",
}

COLORSCALE = [
    [0.00, "#1565C0"],
    [0.25, "#43A047"],
    [0.50, "#FB8C00"],
    [0.75, "#E53935"],
    [1.00, "#7B0000"],
]

def categoria(v):
    if pd.isna(v):    return "Sin dato"
    if v < 0.25:      return "Bajo"
    if v < 0.50:      return "Moderado"
    if v < 0.75:      return "Alto"
    return "Crítico"

# ─────────────────────────────────────────────────────────────────────────────
# 2. CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    #MainMenu { visibility: hidden; }
    header { background: transparent !important; }

    .cinta { height: 6px; width: 100%;
        background: linear-gradient(to right,#00A650 25%,#F9E031 25% 50%,#004F9F 50% 75%,#E30613 75%);
        border-radius: 3px; margin-bottom: 1rem; }

    .kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin: 0.8rem 0 1.2rem; }
    .kpi-card { background: linear-gradient(160deg,#fff 0%,#f0f6ff 100%); border-left: 5px solid #003366;
        padding: 14px 12px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,51,102,.10);
        text-align: center; transition: transform .18s, box-shadow .18s; }
    .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,51,102,.18); }
    .kpi-valor { font-size: clamp(18px,2vw,26px); font-weight: 900; color: #1a2e50; }
    .kpi-titulo { font-size: 10px; color: #6c7a89; font-weight: 700; text-transform: uppercase;
        letter-spacing: .8px; margin-bottom: 4px; }
    .kpi-sub { font-size: 11px; color: #888; margin-top: 2px; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis; }

    /* INFO TAB */
    .hero { background: linear-gradient(135deg,#003366 0%,#004F9F 55%,#0069cc 100%);
        color: white; padding: 36px 30px; border-radius: 14px; margin-bottom: 22px; }
    .hero h1 { font-size: clamp(20px,3vw,34px); font-weight: 900; margin: 0 0 10px; }
    .hero p  { font-size: 15px; opacity: .9; max-width: 720px; line-height: 1.7; margin: 0; }

    .sec { background: white; border-radius: 12px; padding: 24px 26px;
        margin-bottom: 18px; box-shadow: 0 2px 16px rgba(0,0,0,.06); border-top: 4px solid #003366; }
    .sec h2 { color: #003366; font-size: 20px; font-weight: 800; margin-top: 0; }
    .sec p, .sec li { font-size: 14px; color: #444; line-height: 1.7; }

    .idx-card { border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; border-left: 6px solid; }
    .idx-seco   { background: #FFF8E1; border-color: #F57F17; }
    .idx-humedo { background: #E3F2FD; border-color: #1565C0; }
    .idx-card h3 { margin: 0 0 6px; font-size: 15px; font-weight: 800; }
    .idx-seco   h3 { color: #E65100; }
    .idx-humedo h3 { color: #1565C0; }
    .idx-card p { margin: 0; font-size: 13.5px; color: #444; line-height: 1.65; }
    .badge { display:inline-block; font-size:11px; font-weight:700; padding:3px 10px;
        border-radius:20px; margin-top:8px; }
    .bs { background:#FFE0B2; color:#BF360C; }
    .bh { background:#BBDEFB; color:#0D47A1; }

    .ley-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:14px; }
    .ley-item { text-align:center; padding:16px 8px; border-radius:10px; }
    .ley-val { font-size:22px; font-weight:900; }
    .ley-lbl { font-size:12px; font-weight:700; margin-top:4px; }
    .ley-rng { font-size:11px; opacity:.8; }
    .ley-desc { font-size:12px; margin-top:6px; color:#444; }

    @media (max-width:640px) {
        .kpi-grid  { grid-template-columns:repeat(2,1fr); }
        .ley-grid  { grid-template-columns:repeat(2,1fr); }
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geo = json.load(f)
    # Normalizar códigos en GeoJSON
    for feat in geo["features"]:
        p = feat["properties"]
        p["MPIO_CCNCT"] = str(p.get("MPIO_CCNCT", "")).zfill(5)
        p["DPTO_CCDGO"] = str(p.get("DPTO_CCDGO", "")).zfill(2)
    # Construir DataFrame
    rows = [f["properties"] for f in geo["features"]]
    df = pd.DataFrame(rows)
    df["MPIO_CCNCT"] = df["MPIO_CCNCT"].str.zfill(5)
    df["DPTO_CCDGO"] = df["DPTO_CCDGO"].str.zfill(2)
    for col in INDICES.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return geo, df

geo_full, df_full = cargar_datos()

# ─────────────────────────────────────────────────────────────────────────────
# 4. SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="cinta"></div>', unsafe_allow_html=True)
    st.image("https://portal.gestiondelriesgo.gov.co/SiteAssets/logo-ungrd.png", width=140)
    st.markdown("### ⚙️ Filtros de análisis")

    indice_txt = st.selectbox("Índice de afectación:", list(INDICES.keys()))
    indice_col = INDICES[indice_txt]

    deptos = sorted(df_full["DPTO_CNMBR"].dropna().unique())
    depto_sel = st.selectbox("Departamento:", ["Todos"] + list(deptos))

    cat_sel = st.radio(
        "Categoría de riesgo:",
        ["Todas", "Bajo", "Moderado", "Alto", "Crítico"]
    )

    st.markdown("---")
    st.markdown("""**Escala de prioridad:**
<span style="background:#1565C0;color:white;padding:2px 8px;border-radius:12px;font-size:12px">● Bajo</span> 0 – 0.25
<span style="background:#2E7D32;color:white;padding:2px 8px;border-radius:12px;font-size:12px">● Moderado</span> 0.25 – 0.5
<span style="background:#E65100;color:white;padding:2px 8px;border-radius:12px;font-size:12px">● Alto</span> 0.5 – 0.75
<span style="background:#B71C1C;color:white;padding:2px 8px;border-radius:12px;font-size:12px">● Crítico</span> 0.75 – 1""",
        unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 5. TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_visor, tab_info = st.tabs(["🗺️  Visor Interactivo", "📖  Información Técnica"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: VISOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_visor:
    st.markdown('<div class="cinta"></div>', unsafe_allow_html=True)
    st.markdown(f"## 🌡️ {indice_txt}")
    st.caption("Índice normalizado 0–1 por municipio. Mayor valor = mayor prioridad de intervención.")

    # ── Filtrado ──
    df_v = df_full.dropna(subset=[indice_col]).copy()
    if depto_sel != "Todos":
        df_v = df_v[df_v["DPTO_CNMBR"] == depto_sel]
    df_v["Categoría"] = df_v[indice_col].apply(categoria)
    if cat_sel != "Todas":
        df_v = df_v[df_v["Categoría"] == cat_sel]

    # ── GeoJSON activo ──
    if depto_sel != "Todos" and not df_v.empty:
        cod_d = df_v["DPTO_CCDGO"].iloc[0]
        geo_activo = {
            "type": "FeatureCollection",
            "features": [
                f for f in geo_full["features"]
                if f["properties"]["DPTO_CCDGO"] == cod_d
            ],
        }
    else:
        geo_activo = geo_full

    # ── KPIs ──
    n = len(df_v)
    prom = df_v[indice_col].mean() if n > 0 else 0
    maximo = df_v[indice_col].max() if n > 0 else 0
    mun_max = df_v.loc[df_v[indice_col].idxmax(), "MPIO_CNMBR"] if n > 0 else "—"
    pct_alto = (df_v[indice_col] >= 0.50).sum() if n > 0 else 0

    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-titulo">Municipios con dato</div>
        <div class="kpi-valor">{n:,}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-titulo">Índice promedio</div>
        <div class="kpi-valor">{prom:.3f}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-titulo">Índice máximo</div>
        <div class="kpi-valor">{maximo:.3f}</div>
        <div class="kpi-sub">{mun_max}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-titulo">Con riesgo ≥ Alto</div>
        <div class="kpi-valor">{pct_alto}</div>
        <div class="kpi-sub">municipios</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if df_v.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        st.stop()

    # ── Layout mapa / gráfico ──
    col_mapa, col_graf = st.columns([0.55, 0.45])

    with col_mapa:
        # Centro y zoom dinámicos
        if depto_sel != "Todos" and geo_activo["features"]:
            lats, lons = [], []
            for feat in geo_activo["features"]:
                geom = feat["geometry"]
                polys = (
                    geom["coordinates"]
                    if geom["type"] == "Polygon"
                    else [p for mp in geom["coordinates"] for p in [mp[0]]]
                )
                for ring in polys:
                    for c in ring:
                        lons.append(c[0]); lats.append(c[1])
            c_lat = (min(lats) + max(lats)) / 2
            c_lon = (min(lons) + max(lons)) / 2
            span  = max(max(lats)-min(lats), max(lons)-min(lons))
            zoom  = 9 if span < 0.8 else (8 if span < 1.5 else (7 if span < 3 else 6))
        else:
            c_lat, c_lon, zoom = 4.3, -73.0, 4.6

        df_v["_dpto"] = df_v["DPTO_CNMBR"]

        fig_map = px.choropleth_mapbox(
            df_v,
            geojson=geo_activo,
            locations="MPIO_CCNCT",
            featureidkey="properties.MPIO_CCNCT",
            color=indice_col,
            color_continuous_scale=COLORSCALE,
            range_color=[0, 1],
            mapbox_style="carto-positron",
            zoom=zoom,
            center={"lat": c_lat, "lon": c_lon},
            opacity=0.82,
            hover_name="MPIO_CNMBR",
            hover_data={
                "MPIO_CCNCT": False,
                indice_col: False,
                "Categoría": True,
                "_dpto": True,
            },
            labels={"Categoría": "Categoría", "_dpto": "Departamento"},
        )
        fig_map.update_traces(
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                f"{indice_txt}: <b>%{{z:.3f}}</b><br>"
                "Categoría: <b>%{customdata[0]}</b><br>"
                "Depto.: %{customdata[1]}"
                "<extra></extra>"
            )
        )
        fig_map.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=490,
            coloraxis_colorbar=dict(
                title=dict(text="Índice", font=dict(size=11, family="Inter")),
                thickness=12, len=0.7,
                tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                ticktext=["0 Bajo", "0.25", "0.5 Alto", "0.75", "1 Crítico"],
                outlinewidth=0,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(
            fig_map, use_container_width=True,
            config={"displayModeBar": False, "scrollZoom": True}
        )

    with col_graf:
        st.write("")
        df_top = df_v.sort_values(indice_col, ascending=False).head(15).copy()
        df_top["_dpto"] = df_top["DPTO_CNMBR"]

        fig_bar = px.bar(
            df_top,
            x=indice_col,
            y="MPIO_CNMBR",
            orientation="h",
            color=indice_col,
            color_continuous_scale=COLORSCALE,
            range_color=[0, 1],
            title=f"Top 15 municipios – {indice_txt}",
            text=indice_col,
            labels={indice_col: "Índice", "MPIO_CNMBR": ""},
            custom_data=["Categoría", "_dpto"],
        )
        fig_bar.update_traces(
            texttemplate="%{text:.3f}",
            textposition="outside",
            textfont=dict(size=10, family="Inter"),
            marker_line_width=0,
            hovertemplate=(
                "<b>%{y}</b> (%{customdata[1]})<br>"
                "Índice: %{x:.3f}<br>"
                "Categoría: <b>%{customdata[0]}</b>"
                "<extra></extra>"
            ),
        )
        fig_bar.update_layout(
            height=500,
            margin=dict(l=0, r=65, t=40, b=10),
            yaxis=dict(categoryorder="total ascending", tickfont=dict(size=10, family="Inter")),
            coloraxis_showscale=False,
            plot_bgcolor="rgba(248,250,255,0.6)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#2c3e50"),
            title=dict(font=dict(size=13, color="#003366", family="Inter"), x=0.02),
            xaxis=dict(
                range=[0, 1.18],
                tickformat=".2f",
                gridcolor="rgba(200,210,230,0.5)",
                showgrid=True,
                zeroline=False,
                title="",
            ),
            bargap=0.22,
            hoverlabel=dict(bgcolor="white", bordercolor="#003366", font=dict(size=12)),
        )
        st.plotly_chart(
            fig_bar, use_container_width=True,
            config={"displayModeBar": False}
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: INFORMACIÓN TÉCNICA
# ══════════════════════════════════════════════════════════════════════════════
with tab_info:

    st.markdown("""
    <div class="hero">
      <h1>🌡️ Índices de Afectación por el Fenómeno El Niño</h1>
      <p>Herramienta técnico-científica desarrollada por la UNGRD para cuantificar, distribuir geográficamente
      y priorizar el impacto diferencial de El Niño sobre los <strong>1.122 municipios de Colombia</strong>.
      Integra la magnitud histórica de daños con indicadores de vulnerabilidad social y capacidad de respuesta institucional.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── ¿Por qué El Niño? ──
    st.markdown("""
    <div class="sec">
      <h2>🌐 El Niño en Colombia: efectos en el territorio</h2>
      <p>El fenómeno de <strong>El Niño</strong> altera las variables hidrometeorológicas colombianas al asociarse
      con un <strong>déficit de precipitación</strong> y un <strong>aumento de temperatura</strong> derivados del
      calentamiento anómalo del Pacífico ecuatorial. Sus efectos se manifiestan en dos dimensiones:</p>
      <ul>
        <li><strong>Pérdidas directas:</strong> destrucción de infraestructura civil, afectación de personas por
            desabastecimiento de agua, hectáreas de bosque quemadas, pérdida de cultivos y ganado.</li>
        <li><strong>Pérdidas indirectas:</strong> lucro cesante, sobrecostos en energía e industria, brotes
            epidemiológicos por escasez hídrica, deterioro de vías por ausencia de mantenimiento.</li>
      </ul>
      <p>La distribución geográfica exacta de los efectos es compleja: aunque a escala macroclimática el fenómeno
      genera déficit pluviométrico generalizado, la respuesta local está modulada por topografía, ecosistemas y
      microclimatología. Esta heterogeneidad motivó el diseño del <strong>índice multicriterio</strong>.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Metodología ──
    st.markdown("""
    <div class="sec">
      <h2>🔬 Metodología Multicriterio</h2>
      <p>El índice integra tres dimensiones para superar la incertidumbre de los modelos hidrológicos aislados:</p>
      <ol>
        <li><strong>Inventario histórico de afectaciones:</strong> proporción de personas afectadas, damnificadas
            o desplazadas por eventos hidrometeorológicos vinculados a El Niño (sequías, incendios, vendavales, crecientes).</li>
        <li><strong>Vulnerabilidad social territorial:</strong> Índice de Pobreza Multidimensional (IPM), densidad
            poblacional, cobertura de servicios básicos, acceso a agua potable e infraestructura de salud.</li>
        <li><strong>Capacidad de respuesta institucional:</strong> capacidades operativas, técnicas y presupuestales
            de los Consejos Municipales de Gestión del Riesgo (CMGRD).</li>
      </ol>
      <p>El resultado es un <strong>valor normalizado entre 0 y 1</strong> para cada municipio y tipo de evento,
      donde valores mayores indican mayor prioridad de intervención.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Leyenda de categorías ──
    st.markdown("""
    <div class="sec">
      <h2>🎨 Interpretación de Categorías de Riesgo</h2>
      <p>Los valores se clasifican en cuatro niveles de prioridad para la toma de decisiones operativas:</p>
      <div class="ley-grid">
        <div class="ley-item" style="background:#E3F2FD;">
          <div class="ley-val" style="color:#1565C0;">🔵</div>
          <div class="ley-lbl" style="color:#1565C0;">BAJO</div>
          <div class="ley-rng">0.00 – 0.25</div>
          <div class="ley-desc">Afectación histórica mínima. La capacidad local absorbe el impacto sin desbordarse.</div>
        </div>
        <div class="ley-item" style="background:#E8F5E9;">
          <div class="ley-val" style="color:#2E7D32;">🟢</div>
          <div class="ley-lbl" style="color:#2E7D32;">MODERADO</div>
          <div class="ley-rng">0.25 – 0.50</div>
          <div class="ley-desc">Impacto apreciable. Requiere monitoreo activo y planes de contingencia preventivos.</div>
        </div>
        <div class="ley-item" style="background:#FFF3E0;">
          <div class="ley-val" style="color:#E65100;">🟠</div>
          <div class="ley-lbl" style="color:#E65100;">ALTO</div>
          <div class="ley-rng">0.50 – 0.75</div>
          <div class="ley-desc">Fragilidad acumulada significativa. Intervención técnica preventiva prioritaria.</div>
        </div>
        <div class="ley-item" style="background:#FFEBEE;">
          <div class="ley-val" style="color:#B71C1C;">🔴</div>
          <div class="ley-lbl" style="color:#B71C1C;">CRÍTICO</div>
          <div class="ley-rng">0.75 – 1.00</div>
          <div class="ley-desc">Alta probabilidad de daño severo. Intervención urgente con apoyo nacional requerido.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Los 9 índices ──
    st.markdown('<div class="sec"><h2>📊 Los 9 Índices de Afectación</h2>', unsafe_allow_html=True)

    st.markdown("""
    <p><strong style="color:#E65100;font-size:15px;">☀️ Eventos en condiciones secas (El Niño directo)</strong></p>

    <div class="idx-card idx-seco">
      <h3>🔥 Incendios Forestales <small style="font-weight:400;color:#888;">(I_IF · 729 municipios)</small></h3>
      <p>Evalúa la exposición histórica a incendios de cobertura vegetal. Integra la proporción de hectáreas
      quemadas respecto a la superficie boscosa municipal, la frecuencia histórica de eventos y la vulnerabilidad
      territorial. Es el índice de mayor cobertura geográfica por la distribución generalizada del riesgo durante
      El Niño a lo largo de todo el país.</p>
      <span class="badge bs">☀️ Condición seca</span>
    </div>

    <div class="idx-card idx-seco">
      <h3>💧 Desabastecimiento de Agua <small style="font-weight:400;color:#888;">(I_Desabast · 130 municipios)</small></h3>
      <p>Cuantifica el riesgo de desabastecimiento hídrico a la población. Combina la proporción de personas
      afectadas históricamente con indicadores de cobertura de acueducto, disponibilidad hídrica per cápita y
      dependencia de fuentes superficiales susceptibles a sequía. Afecta principalmente municipios rurales con
      infraestructura hídrica precaria y alta dependencia de ríos estacionales.</p>
      <span class="badge bs">☀️ Condición seca</span>
    </div>

    <div class="idx-card idx-seco">
      <h3>☀️ Daño Hidrológico por Sequía <small style="font-weight:400;color:#888;">(I_DHTS_I_D · 205 municipios)</small></h3>
      <p>Índice compuesto que integra los daños hidrotecnológicos asociados a condiciones de sequía, incluyendo
      impactos en infraestructura hidráulica, producción agropecuaria, pérdida de biodiversidad acuática e
      interrupción de servicios energéticos hidroeléctricos. Complementa al índice de incendios capturando efectos
      difusos en el subsistema hídrico.</p>
      <span class="badge bs">☀️ Condición seca</span>
    </div>

    <p style="margin-top:22px;"><strong style="color:#1565C0;font-size:15px;">🌧️ Eventos en condiciones húmedas (respuesta paradójica de El Niño)</strong></p>
    <p style="font-size:13px;color:#555;">Aunque El Niño se asocia a déficit pluviométrico, en ciertas regiones y temporadas intensifica la convección local, generando eventos de precipitación extrema localizada.</p>

    <div class="idx-card idx-humedo">
      <h3>🌊 Inundaciones <small style="font-weight:400;color:#888;">(I_Inundaci · 206 municipios)</small></h3>
      <p>Mide la afectación por inundaciones de lenta evolución (anegamiento prolongado). La criticidad máxima se
      concentra en el Pacífico colombiano y la depresión momposina (región de La Mojana), donde la dinámica de los
      ríos Cauca, San Jorge y Magdalena afecta comunidades con alta vulnerabilidad socioeconómica. Estrategia:
      macroproyectos de adaptación climática, infraestructura resiliente (palafítica, diques con compuertas) y
      reubicación de poblaciones en zonas de inmersión recurrente.</p>
      <span class="badge bh">🌧️ Condición húmeda</span>
    </div>

    <div class="idx-card idx-humedo">
      <h3>💨 Vendavales <small style="font-weight:400;color:#888;">(I_Vendaval · 281 municipios)</small></h3>
      <p>Evalúa el impacto de vientos fuertes sobre la infraestructura habitacional. La criticidad máxima se
      concentra en el litoral Pacífico (Chocó) y enclaves del Caribe, donde ráfagas convectivas impactan viviendas
      con cubiertas ligeras sin anclaje técnico (zinc, asbesto-cemento, caña). La región Andina muestra alta
      densidad de eventos pero menor afectación relativa gracias a mayor solidez constructiva.</p>
      <span class="badge bh">🌧️ Condición húmeda</span>
    </div>

    <div class="idx-card idx-humedo">
      <h3>⛰️ Movimientos en Masa <small style="font-weight:400;color:#888;">(I_MovMasa · 119 municipios)</small></h3>
      <p>Integra la frecuencia histórica de deslizamientos, flujos de detritos y caídas de roca con indicadores
      de pendiente del terreno, litología, cobertura vegetal degradada e intervención antrópica. Los municipios de
      mayor índice corresponden a zonas cordilleranas con alta deforestación y precipitaciones acumuladas intensas.
      Requiere gestión correctiva mediante rondas hídricas y obras de bioingeniería.</p>
      <span class="badge bh">🌧️ Condición húmeda</span>
    </div>

    <div class="idx-card idx-humedo">
      <h3>🏞️ Crecientes Súbitas <small style="font-weight:400;color:#888;">(I_Crecient · 45 municipios)</small></h3>
      <p>Captura el riesgo de desbordamiento repentino en cuencas de alta pendiente. La criticidad alta se
      concentra en el piedemonte llanero y amazónico, y en sectores del Pacífico, donde las descargas súbitas
      impactan comunidades ribereñas. Los ramales andinos centrales (Antioquia, Eje Cafetero, Cundinamarca) muestran
      alta frecuencia pero baja afectación relativa por mayor capacidad local de absorción. Estrategia: rondas
      hídricas y gobernanza territorial preventiva.</p>
      <span class="badge bh">🌧️ Condición húmeda</span>
    </div>

    <div class="idx-card idx-humedo">
      <h3>⚡ Avenidas Torrenciales <small style="font-weight:400;color:#888;">(I_AVT · 23 municipios)</small></h3>
      <p>Evalúa el riesgo de flujos de masa hiperconcentrados en cuencas torrenciales de montaña. Con solo 23
      municipios con registro histórico significativo, refleja la alta especialización geomorfológica del evento.
      La violencia y rapidez del fenómeno hacen que los municipios identificados requieran Sistemas de Alerta
      Temprana (SAT) instrumentales comunitarios con la máxima urgencia.</p>
      <span class="badge bh">🌧️ Condición húmeda</span>
    </div>

    <div class="idx-card idx-humedo">
      <h3>🌧️ Daño Hidrológico por Lluvias <small style="font-weight:400;color:#888;">(I_DHTLL_In · 254 municipios)</small></h3>
      <p>Índice compuesto que agrega los daños hidrotecnológicos generados por exceso de precipitación: impactos
      en infraestructura vial (vías terciarias sin drenaje), sistemas de acueducto y alcantarillado, equipamiento
      comunitario y pérdidas agropecuarias por exceso hídrico. Con 254 municipios, es el índice húmedo de mayor
      cobertura territorial y uno de los más relevantes para la planificación sectorial.</p>
      <span class="badge bh">🌧️ Condición húmeda</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Usos y aplicaciones ──
    st.markdown("""
    <div class="sec">
      <h2>🎯 Usos y aplicaciones del visor</h2>
      <ul>
        <li><strong>Focalización de recursos:</strong> priorizar la asignación de recursos financieros y técnicos
            hacia municipios con mayor fragilidad acumulada antes de la temporada seca.</li>
        <li><strong>Ayuda humanitaria anticipatoria:</strong> identificar territorios para preposicionamiento de
            kits de emergencia y brigadas de respuesta.</li>
        <li><strong>Planificación sectorial:</strong> orientar inversiones en infraestructura resiliente, Sistemas
            de Alerta Temprana (SAT) y ordenamiento territorial (POT/PMGRD).</li>
        <li><strong>Comunicación del riesgo:</strong> proveer información objetiva a gobernaciones, alcaldías,
            medios de comunicación y sociedad civil sobre territorios prioritarios.</li>
        <li><strong>Seguimiento y evaluación:</strong> evaluar la evolución de la vulnerabilidad territorial a
            medida que se actualicen los registros históricos de daños.</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer ──
    st.markdown("""
    <div style="margin-top:30px;padding:20px;background:#f8f9fa;border-radius:10px;
        border-top:3px solid #003366;font-size:13px;color:#495057;">
      <b>Fuentes y créditos técnicos:</b>
      <ul>
        <li>Registros históricos de emergencias: Sala de Crisis UNGRD.</li>
        <li>Índice de Pobreza Multidimensional: DANE.</li>
        <li>Cartografía oficial: IGAC / DANE – DIVIPOLA.</li>
      </ul>
      <b>Elaborado por:</b> Christian Euscátegui — Subdirección para el Conocimiento del Riesgo (SCR / UNGRD)<br>
      <b>Junio de 2026</b>
    </div>
    """, unsafe_allow_html=True)
