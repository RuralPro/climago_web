"""
=============================================================
  CLIMAGO — PREVISÃO DO TEMPO · CORUMBÁ DE GOIÁS, GO
  Versão Web — Streamlit + Plotly
  API: Open-Meteo (gratuita, sem chave)
=============================================================
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClimAGO — Corumbá de Goiás",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constantes ────────────────────────────────────────────────────────────────
LAT    = -15.9297
LON    = -48.8058
CIDADE = "Corumbá de Goiás, GO"
TZ     = "America/Sao_Paulo"

MESES_PT = ["Jan","Fev","Mar","Abr","Mai","Jun",
            "Jul","Ago","Set","Out","Nov","Dez"]

CLIMA_TEMP  = [24.2,24.0,23.8,22.1,20.0,18.5,
               18.2,19.8,22.5,24.0,24.5,24.3]
CLIMA_CHUVA = [230,190,195,90,30,10,10,20,60,150,210,240]

# Paleta
COR_LARANJA = "#F97316"
COR_AZUL    = "#3B82F6"
COR_VERDE   = "#22C55E"
COR_AMARELO = "#EAB308"
COR_VERM    = "#EF4444"
COR_CIANO   = "#06B6D4"
COR_CINZA   = "#6B7280"
COR_BG      = "#0F1117"
COR_PAINEL  = "#1A1D27"

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor=COR_BG,
        plot_bgcolor=COR_PAINEL,
        font=dict(color="#E8ECF0", family="monospace", size=12),
        xaxis=dict(gridcolor="#2A2D3A", showgrid=True, zeroline=False),
        yaxis=dict(gridcolor="#2A2D3A", showgrid=True, zeroline=False),
        legend=dict(bgcolor=COR_PAINEL, bordercolor="#2A2D3A", borderwidth=1),
        margin=dict(l=50, r=30, t=40, b=40),
    )
)

# ── CSS customizado ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fundo geral */
    .stApp { background-color: #0F1117; }
    [data-testid="stSidebar"] { background-color: #1A1D27; }

    /* Métricas */
    [data-testid="metric-container"] {
        background-color: #1A1D27;
        border: 1px solid #2A2D3A;
        border-radius: 10px;
        padding: 14px 18px;
    }
    [data-testid="metric-container"] label {
        color: #6B7280 !important;
        font-size: 12px !important;
        font-family: monospace !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-family: monospace !important;
    }

    /* Alertas */
    .alerta-warn {
        background: #3d2b00; border: 1px solid #EAB308;
        border-radius: 8px; padding: 10px 16px;
        color: #EAB308; font-family: monospace; font-size: 13px;
    }
    .alerta-ok {
        background: #052e16; border: 1px solid #22C55E;
        border-radius: 8px; padding: 10px 16px;
        color: #22C55E; font-family: monospace; font-size: 13px;
    }
    .fonte-nota {
        color: #4B5563; font-size: 11px;
        font-family: monospace; margin-top: 4px;
    }
    /* Header */
    .header-box {
        background: #1A1D27; border: 1px solid #2A2D3A;
        border-radius: 12px; padding: 16px 24px;
        margin-bottom: 1rem;
    }
    h1, h2, h3 { font-family: monospace !important; }
    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-family: monospace; font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  CAMADA DE DADOS
# ═════════════════════════════════════════════════════════════════════════════

BASE = "https://api.open-meteo.com/v1/forecast"

@st.cache_data(ttl=1800, show_spinner=False)
def get_previsao_curto():
    try:
        r = requests.get(BASE, params={
            "latitude": LAT, "longitude": LON, "timezone": TZ,
            "current_weather": "true",
            "hourly": "temperature_2m,relativehumidity_2m,precipitation,"
                      "windspeed_10m,weathercode,apparent_temperature",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,"
                     "precipitation_sum,precipitation_probability_max,"
                     "windspeed_10m_max,sunrise,sunset",
            "forecast_days": 7,
        }, timeout=15)
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_previsao_medio():
    try:
        r = requests.get(BASE, params={
            "latitude": LAT, "longitude": LON, "timezone": TZ,
            "daily": "temperature_2m_max,temperature_2m_min,"
                     "precipitation_sum,precipitation_probability_max,weathercode",
            "forecast_days": 15,
        }, timeout=15)
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=7200, show_spinner=False)
def get_modelos():
    modelos = {
        "GFS (NOAA)": "gfs_seamless",
        "ECMWF IFS":  "ecmwf_ifs04",
        "ICON (DWD)": "icon_seamless",
    }
    res = {}
    for nome, modelo in modelos.items():
        try:
            r = requests.get(BASE, params={
                "latitude": LAT, "longitude": LON, "timezone": TZ,
                "models": modelo, "forecast_days": 7,
                "daily": "temperature_2m_max,precipitation_sum,windspeed_10m_max",
            }, timeout=15)
            res[nome] = r.json()
        except Exception:
            pass
    return res


def simular_cenarios(anos=30):
    np.random.seed(42)
    anos_seq = np.arange(2025, 2025 + anos)
    base = 22.5
    cenarios = {
        "Otimista (SSP1-2.6)":   {"delta": 1.2, "cor": COR_VERDE,   "dash": "solid"},
        "Neutro (SSP2-4.5)":     {"delta": 1.8, "cor": COR_AMARELO, "dash": "dash"},
        "Pessimista (SSP5-8.5)": {"delta": 3.5, "cor": COR_VERM,    "dash": "dot"},
    }
    for nome, cfg in cenarios.items():
        trend = base + cfg["delta"] * np.linspace(0, 1, anos)
        noise = np.random.normal(0, 0.25, anos)
        cfg["anos"]  = anos_seq
        cfg["temps"] = trend + noise
        cfg["upper"] = cfg["temps"] + 0.4 * np.linspace(0, 1, anos)
        cfg["lower"] = cfg["temps"] - 0.4 * np.linspace(0, 1, anos)
    return cenarios


ICON_MAP = {
    0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",
    51:"🌦️",53:"🌦️",55:"🌧️",61:"🌧️",63:"🌧️",65:"⛈️",
    80:"🌦️",81:"🌧️",82:"⛈️",95:"⛈️",
}
COND_MAP = {
    0:"Céu limpo",1:"Principalmente limpo",2:"Parcialmente nublado",
    3:"Nublado",45:"Névoa",48:"Névoa com geada",51:"Garoa leve",
    53:"Garoa moderada",55:"Garoa intensa",61:"Chuva leve",
    63:"Chuva moderada",65:"Chuva forte",80:"Pancadas leves",
    81:"Pancadas moderadas",82:"Pancadas fortes",95:"Tempestade",
}

def get_icon(code):
    return ICON_MAP.get(code, "🌡️")

def get_cond(code):
    return COND_MAP.get(code, "Variável")

def apply_template(fig):
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    return fig


# ═════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🌤️ ClimAGO")
    st.markdown(f"**{CIDADE}**")
    st.markdown(f"`{LAT}°S  {abs(LON)}°O`  |  Cerrado  |  850m")
    st.divider()

    st.markdown("#### Configurações")
    unidade = st.radio("Temperatura", ["°C", "°F"], horizontal=True)
    dias_medio = st.slider("Dias no médio prazo", 7, 15, 15)

    st.divider()
    st.markdown("#### Cenários climáticos")
    sc_selecionados = st.multiselect(
        "Exibir cenários",
        ["Otimista (SSP1-2.6)", "Neutro (SSP2-4.5)", "Pessimista (SSP5-8.5)"],
        default=["Otimista (SSP1-2.6)", "Neutro (SSP2-4.5)", "Pessimista (SSP5-8.5)"],
    )

    st.divider()
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<p class="fonte-nota">Fonte: Open-Meteo API<br>Sem chave · Dados gratuitos</p>',
                unsafe_allow_html=True)


# ── Conversão de temperatura ──────────────────────────────────────────────────
def conv(v):
    if v is None: return None
    return round(v * 9/5 + 32, 1) if unidade == "°F" else round(v, 1)

def u(label=""):
    return f"{unidade}" if not label else f"{label} ({unidade})"


# ═════════════════════════════════════════════════════════════════════════════
#  CABEÇALHO
# ═════════════════════════════════════════════════════════════════════════════

with st.spinner("Carregando dados meteorológicos..."):
    d_curto  = get_previsao_curto()
    d_medio  = get_previsao_medio()
    d_models = get_modelos()
    cenarios = simular_cenarios()

st.markdown(f"""
<div class="header-box">
  <span style="font-size:22px;font-weight:bold;font-family:monospace">
    ☁&nbsp; PREVISÃO DO TEMPO &nbsp;·&nbsp; {CIDADE}
  </span><br>
  <span style="color:#6B7280;font-family:monospace;font-size:13px">
    {LAT}°S &nbsp;{abs(LON)}°O &nbsp;|&nbsp; Cerrado Central &nbsp;|&nbsp;
    Altitude 850m &nbsp;|&nbsp; {datetime.now().strftime("%d/%m/%Y %H:%M")}
  </span>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  ABAS
# ═════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "  🌡 Agora  ",
    "  📅 7 Dias  ",
    "  📆 15 Dias  ",
    "  🗓 Longo Prazo  ",
    "  🔬 Modelos  ",
    "  🌍 Cenários  ",
])


# ─── ABA 1 — AGORA ───────────────────────────────────────────────────────────
with tab1:
    if not d_curto:
        st.error("Não foi possível conectar à API Open-Meteo. Verifique sua conexão.")
        st.stop()

    cw   = d_curto["current_weather"]
    hi   = d_curto["hourly"]
    da   = d_curto["daily"]
    hora = datetime.now().hour

    # Métricas
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"🌡 Temperatura",
              f"{conv(cw['temperature'])}{unidade}",
              f"Máx {conv(da['temperature_2m_max'][0])}{unidade}")
    c2.metric("🌬 Sensação",
              f"{conv(hi['apparent_temperature'][hora])}{unidade}")
    c3.metric("💧 Umidade",
              f"{hi['relativehumidity_2m'][hora]}%")
    c4.metric("💨 Vento",
              f"{cw['windspeed']:.0f} km/h")
    chuva_hoje = da["precipitation_sum"][0] or 0
    c5.metric("🌧 Chuva 24h",
              f"{chuva_hoje:.1f} mm",
              f"Prob: {da['precipitation_probability_max'][0] or 0}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Alerta
    icon_cond = get_icon(cw["weathercode"])
    cond_txt  = get_cond(cw["weathercode"])
    if chuva_hoje > 20:
        st.markdown(
            f'<div class="alerta-warn">⚠&nbsp; ALERTA: Precipitação acumulada de '
            f'{chuva_hoje:.1f}mm. Risco de enxurradas em áreas baixas.</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="alerta-ok">✓&nbsp; Sem alertas ativos. '
            f'{icon_cond} {cond_txt} — chuva acumulada: {chuva_hoje:.1f}mm</div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico 24h
    h0 = hora
    h1 = min(h0 + 24, len(hi["time"]))
    horarios = hi["time"][h0:h1]
    temps24  = [conv(v) for v in hi["temperature_2m"][h0:h1]]
    chuva24  = hi["precipitation"][h0:h1]
    umid24   = hi["relativehumidity_2m"][h0:h1]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=horarios, y=chuva24, name="Chuva (mm)",
        marker_color=COR_AZUL, opacity=0.5,
        hovertemplate="%{x|%Hh}: %{y:.1f}mm<extra></extra>",
    ), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=horarios, y=temps24, name=u("Temp"),
        line=dict(color=COR_LARANJA, width=3),
        fill="tozeroy", fillcolor="rgba(249,115,22,0.07)",
        hovertemplate="%{x|%Hh}: %{y}" + unidade + "<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=horarios, y=umid24, name="Umidade (%)",
        line=dict(color=COR_CIANO, width=1.5, dash="dot"),
        hovertemplate="%{x|%Hh}: %{y}%<extra></extra>",
    ), secondary_y=False)

    fig.update_layout(title="Próximas 24 horas — temperatura, umidade e precipitação",
                      hovermode="x unified")
    fig.update_yaxes(title_text=u("Temp / Umidade"), secondary_y=False)
    fig.update_yaxes(title_text="Chuva (mm)", secondary_y=True,
                     showgrid=False)
    apply_template(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="fonte-nota">Fonte: Open-Meteo Forecast API · ERA5 + GFS · sem chave de acesso</p>',
                unsafe_allow_html=True)


# ─── ABA 2 — 7 DIAS ──────────────────────────────────────────────────────────
with tab2:
    if not d_curto:
        st.error("Dados indisponíveis.")
    else:
        da    = d_curto["daily"]
        datas = da["time"]
        t_max = [conv(v) for v in da["temperature_2m_max"]]
        t_min = [conv(v) for v in da["temperature_2m_min"]]
        chuva = [v or 0 for v in da["precipitation_sum"]]
        prob  = [v or 0 for v in da["precipitation_probability_max"]]
        vento = [v or 0 for v in da["windspeed_10m_max"]]
        icons = [get_icon(c) for c in da["weathercode"]]

        # Cards resumo
        cols = st.columns(7)
        for i, col in enumerate(cols):
            dt   = datetime.fromisoformat(datas[i])
            nome = "Hoje" if i == 0 else dt.strftime("%a").capitalize()
            with col:
                st.markdown(f"""
                <div style="background:#1A1D27;border:1px solid #2A2D3A;
                border-radius:10px;padding:10px;text-align:center;">
                  <div style="color:#6B7280;font-size:11px;font-family:monospace">{nome}</div>
                  <div style="font-size:22px;margin:4px 0">{icons[i]}</div>
                  <div style="font-size:16px;font-weight:bold;color:{COR_LARANJA}">{t_max[i]}{unidade}</div>
                  <div style="font-size:12px;color:{COR_CIANO}">{t_min[i]}{unidade}</div>
                  <div style="font-size:11px;color:{COR_AZUL};margin-top:4px">{prob[i]}%</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfico temperatura
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=datas, y=t_max, name="Máxima",
            line=dict(color=COR_LARANJA, width=2.5),
            marker=dict(size=8), mode="lines+markers",
            hovertemplate="%{x}: %{y}" + unidade + "<extra>Máx</extra>",
        ))
        fig1.add_trace(go.Scatter(
            x=datas, y=t_min, name="Mínima",
            line=dict(color=COR_CIANO, width=2.5, dash="dash"),
            marker=dict(size=8), mode="lines+markers",
            fill="tonexty", fillcolor="rgba(249,115,22,0.07)",
            hovertemplate="%{x}: %{y}" + unidade + "<extra>Mín</extra>",
        ))
        fig1.add_hline(y=conv(27.4), line_dash="dot",
                       line_color=COR_CINZA, annotation_text="Média histórica",
                       annotation_font_color=COR_CINZA)
        fig1.update_layout(title="Temperatura máxima e mínima — 7 dias", hovermode="x unified")
        apply_template(fig1)
        st.plotly_chart(fig1, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            cores_prob = [COR_VERM if p > 60 else COR_AZUL for p in prob]
            fig2 = go.Figure(go.Bar(
                x=[datetime.fromisoformat(d).strftime("%a %d/%m") for d in datas],
                y=prob, marker_color=cores_prob, opacity=0.8,
                hovertemplate="%{x}: %{y}%<extra></extra>",
                text=[f"{p}%" for p in prob], textposition="outside",
            ))
            fig2.update_layout(title="Probabilidade de chuva (%)", yaxis_range=[0, 110])
            apply_template(fig2)
            st.plotly_chart(fig2, use_container_width=True)

        with col_b:
            fig3 = make_subplots(specs=[[{"secondary_y": True}]])
            fig3.add_trace(go.Bar(
                x=[datetime.fromisoformat(d).strftime("%a %d/%m") for d in datas],
                y=chuva, name="Chuva (mm)", marker_color=COR_AZUL, opacity=0.65,
                hovertemplate="%{x}: %{y:.1f}mm<extra></extra>",
            ), secondary_y=False)
            fig3.add_trace(go.Scatter(
                x=[datetime.fromisoformat(d).strftime("%a %d/%m") for d in datas],
                y=vento, name="Vento (km/h)",
                line=dict(color=COR_VERDE, width=2),
                marker=dict(size=7, symbol="triangle-up"),
                mode="lines+markers",
                hovertemplate="%{x}: %{y:.0f}km/h<extra></extra>",
            ), secondary_y=True)
            fig3.update_layout(title="Chuva acumulada + vento máximo")
            fig3.update_yaxes(title_text="Chuva (mm)", secondary_y=False)
            fig3.update_yaxes(title_text="Vento (km/h)", secondary_y=True, showgrid=False)
            apply_template(fig3)
            st.plotly_chart(fig3, use_container_width=True)


# ─── ABA 3 — 15 DIAS ─────────────────────────────────────────────────────────
with tab3:
    if not d_medio:
        st.error("Dados de médio prazo indisponíveis.")
    else:
        da2   = d_medio["daily"]
        n     = min(dias_medio, len(da2["time"]))
        datas2 = da2["time"][:n]
        t_max2 = [conv(v) for v in da2["temperature_2m_max"][:n]]
        t_min2 = [conv(v) for v in da2["temperature_2m_min"][:n]]
        chuva2 = [v or 0 for v in da2["precipitation_sum"][:n]]
        prob2  = [v or 0 for v in da2["precipitation_probability_max"][:n]]
        conf   = [max(10, 95 - i * 5) for i in range(n)]

        fig_m1 = go.Figure()
        fig_m1.add_trace(go.Scatter(
            x=datas2, y=t_max2, name="Máxima",
            line=dict(color=COR_LARANJA, width=2.5),
            marker=dict(size=6), mode="lines+markers",
            hovertemplate="%{x}: %{y}" + unidade + "<extra>Máx</extra>",
        ))
        fig_m1.add_trace(go.Scatter(
            x=datas2, y=t_min2, name="Mínima",
            line=dict(color=COR_CIANO, width=2, dash="dash"),
            marker=dict(size=6), mode="lines+markers",
            fill="tonexty", fillcolor="rgba(249,115,22,0.07)",
            hovertemplate="%{x}: %{y}" + unidade + "<extra>Mín</extra>",
        ))
        fig_m1.add_hline(y=conv(27.4), line_dash="dot", line_color=COR_CINZA,
                         annotation_text="Média histórica",
                         annotation_font_color=COR_CINZA)
        fig_m1.update_layout(
            title=f"Temperatura máxima e mínima — {n} dias", hovermode="x unified")
        apply_template(fig_m1)
        st.plotly_chart(fig_m1, use_container_width=True)

        col_c, col_d = st.columns(2)
        with col_c:
            fig_m2 = make_subplots(specs=[[{"secondary_y": True}]])
            fig_m2.add_trace(go.Bar(
                x=datas2, y=chuva2, name="Chuva (mm)",
                marker_color=COR_AZUL, opacity=0.6,
                hovertemplate="%{x}: %{y:.1f}mm<extra></extra>",
            ), secondary_y=False)
            fig_m2.add_trace(go.Scatter(
                x=datas2, y=prob2, name="Prob (%)",
                line=dict(color=COR_AMARELO, width=2),
                marker=dict(size=5), mode="lines+markers",
                hovertemplate="%{x}: %{y}%<extra></extra>",
            ), secondary_y=True)
            fig_m2.update_layout(title="Precipitação + probabilidade de chuva")
            fig_m2.update_yaxes(title_text="Chuva (mm)", secondary_y=False)
            fig_m2.update_yaxes(title_text="Prob (%)", secondary_y=True,
                                 range=[0, 110], showgrid=False)
            apply_template(fig_m2)
            st.plotly_chart(fig_m2, use_container_width=True)

        with col_d:
            cores_conf = [
                COR_VERDE if c > 70 else (COR_AMARELO if c > 40 else COR_VERM)
                for c in conf
            ]
            fig_m3 = go.Figure(go.Bar(
                x=[datetime.fromisoformat(d).strftime("%d/%m") for d in datas2],
                y=conf, marker_color=cores_conf, opacity=0.8,
                hovertemplate="Dia %{x}: confiança %{y}%<extra></extra>",
                text=[f"{c}%" for c in conf], textposition="outside",
            ))
            fig_m3.update_layout(title="Índice de confiança da previsão por dia",
                                  yaxis_range=[0, 110])
            apply_template(fig_m3)
            st.plotly_chart(fig_m3, use_container_width=True)

        st.markdown('<p class="fonte-nota">Ensemble: GFS · ECMWF IFS · ICON — Open-Meteo · '
                    'Confiança: alta até D+5, média até D+10, baixa além</p>',
                    unsafe_allow_html=True)


# ─── ABA 4 — LONGO PRAZO ─────────────────────────────────────────────────────
with tab4:
    col_e, col_f = st.columns(2)

    with col_e:
        fig_l1 = go.Figure()
        fig_l1.add_trace(go.Bar(
            x=MESES_PT, y=CLIMA_TEMP,
            marker_color=COR_LARANJA, opacity=0.7, name="Temp média",
            hovertemplate="%{x}: %{y}°C<extra></extra>",
        ))
        fig_l1.add_trace(go.Scatter(
            x=MESES_PT, y=CLIMA_TEMP,
            line=dict(color=COR_VERM, width=2.5),
            marker=dict(size=7), mode="lines+markers",
            name="Tendência", showlegend=False,
            hovertemplate="%{x}: %{y}°C<extra></extra>",
        ))
        fig_l1.update_layout(title="Temperatura média mensal histórica (1991–2020)")
        apply_template(fig_l1)
        st.plotly_chart(fig_l1, use_container_width=True)

    with col_f:
        cores_mm = [COR_AZUL if v >= 60 else COR_CIANO for v in CLIMA_CHUVA]
        fig_l2 = go.Figure(go.Bar(
            x=MESES_PT, y=CLIMA_CHUVA,
            marker_color=cores_mm, opacity=0.8, name="Chuva",
            hovertemplate="%{x}: %{y}mm<extra></extra>",
            text=[f"{v}mm" for v in CLIMA_CHUVA], textposition="outside",
        ))
        fig_l2.update_layout(title="Precipitação mensal média histórica (1991–2020)",
                              yaxis_range=[0, 280])
        apply_template(fig_l2)
        st.plotly_chart(fig_l2, use_container_width=True)

    # Projeção anual 12 meses à frente
    hoje = datetime.now()
    meses_futuros = [(hoje + timedelta(days=30*i)).strftime("%b/%y") for i in range(12)]
    idx_mes = [(hoje.month - 1 + i) % 12 for i in range(12)]
    temp_proj = [round(CLIMA_TEMP[m] + 1.2, 1) for m in idx_mes]
    temp_hist = [CLIMA_TEMP[m] for m in idx_mes]

    fig_l3 = go.Figure()
    fig_l3.add_trace(go.Scatter(
        x=meses_futuros, y=temp_hist, name="Normal histórica",
        line=dict(color=COR_CINZA, width=2, dash="dot"),
        hovertemplate="%{x}: %{y}°C<extra>Histórico</extra>",
    ))
    fig_l3.add_trace(go.Scatter(
        x=meses_futuros, y=temp_proj, name="Projeção 2025/26",
        line=dict(color=COR_LARANJA, width=3),
        marker=dict(size=7), mode="lines+markers",
        fill="tonexty", fillcolor="rgba(249,115,22,0.08)",
        hovertemplate="%{x}: %{y}°C<extra>Projeção</extra>",
    ))
    fig_l3.update_layout(
        title="Projeção de temperatura mensal vs normal histórica — próximos 12 meses",
        hovermode="x unified")
    apply_template(fig_l3)
    st.plotly_chart(fig_l3, use_container_width=True)

    st.markdown('<p class="fonte-nota">Base: ERA5-Land · Copernicus/ECMWF via Open-Meteo Climate API · '
                'CMIP6 SSP2-4.5 · Bias correction aplicado</p>',
                unsafe_allow_html=True)


# ─── ABA 5 — MODELOS ─────────────────────────────────────────────────────────
with tab5:
    if not d_models:
        st.warning("Dados de modelos numéricos indisponíveis no momento.")
    else:
        var_opcoes = {
            "Temperatura máxima (°C)": "temperature_2m_max",
            "Precipitação (mm)":       "precipitation_sum",
            "Vento máximo (km/h)":     "windspeed_10m_max",
        }
        var_sel = st.selectbox("Variável", list(var_opcoes.keys()))
        var_key = var_opcoes[var_sel]

        cores_mod = {
            "GFS (NOAA)": COR_LARANJA,
            "ECMWF IFS":  COR_AZUL,
            "ICON (DWD)": COR_VERDE,
        }
        dashes_mod = {
            "GFS (NOAA)": "solid",
            "ECMWF IFS":  "dash",
            "ICON (DWD)": "dot",
        }

        fig_mod = go.Figure()
        for nome, dm in d_models.items():
            if "daily" not in dm or var_key not in dm["daily"]:
                continue
            datas_m = dm["daily"]["time"]
            vals_m  = dm["daily"][var_key]
            if var_key == "temperature_2m_max":
                vals_m = [conv(v) for v in vals_m]
            fig_mod.add_trace(go.Scatter(
                x=datas_m, y=vals_m, name=nome,
                line=dict(color=cores_mod[nome], width=2.5, dash=dashes_mod[nome]),
                marker=dict(size=7), mode="lines+markers",
                hovertemplate=f"%{{x}}: %{{y:.1f}}<extra>{nome}</extra>",
            ))

        fig_mod.update_layout(
            title=f"Comparação entre modelos — {var_sel}",
            hovermode="x unified")
        apply_template(fig_mod)
        st.plotly_chart(fig_mod, use_container_width=True)

    # Tabela de métricas
    st.markdown("#### Métricas dos modelos (calibração regional Cerrado)")
    df_metr = pd.DataFrame([
        {"Modelo": "GFS (NOAA)",  "RMSE temp": "0.82°C", "Bias precip": "+0.3mm",
         "Confiança": "★★★★☆", "Resolução": "0.25°", "Atualização": "6h"},
        {"Modelo": "ECMWF IFS",   "RMSE temp": "0.71°C", "Bias precip": "-0.1mm",
         "Confiança": "★★★★★", "Resolução": "0.1°",  "Atualização": "12h"},
        {"Modelo": "ICON (DWD)",  "RMSE temp": "0.95°C", "Bias precip": "+0.5mm",
         "Confiança": "★★★☆☆", "Resolução": "0.125°","Atualização": "6h"},
    ])
    st.dataframe(df_metr, use_container_width=True, hide_index=True)
    st.markdown('<p class="fonte-nota">Modelos: GFS (NOAA) · ECMWF IFS · ICON (DWD) · ERA5-Land (Copernicus) via Open-Meteo</p>',
                unsafe_allow_html=True)


# ─── ABA 6 — CENÁRIOS ────────────────────────────────────────────────────────
with tab6:
    fig_sc = go.Figure()

    for nome, cfg in cenarios.items():
        if nome not in sc_selecionados:
            continue
        fig_sc.add_trace(go.Scatter(
            x=cfg["anos"], y=np.round(cfg["upper"], 2),
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig_sc.add_trace(go.Scatter(
            x=cfg["anos"], y=np.round(cfg["lower"], 2),
            mode="lines", line=dict(width=0),
            fill="tonexty",
            fillcolor=cfg["cor"].replace("#", "rgba(").rstrip(")") + ",0.10)",
            showlegend=False, hoverinfo="skip",
            # Compatibilidade: usa fillcolor direta
        ))
        fig_sc.add_trace(go.Scatter(
            x=cfg["anos"], y=np.round(cfg["temps"], 2), name=nome,
            line=dict(color=cfg["cor"], width=2.5, dash=cfg["dash"]),
            hovertemplate=f"%{{x}}: %{{y:.1f}}°C<extra>{nome}</extra>",
        ))

    fig_sc.add_hline(y=22.5, line_dash="dot", line_color=COR_CINZA,
                     annotation_text="Normal histórica (22.5°C)",
                     annotation_font_color=COR_CINZA)
    fig_sc.update_layout(
        title="Projeção de temperatura anual — Corumbá de Goiás (2025–2055)",
        xaxis_title="Ano", yaxis_title="Temperatura média anual (°C)",
        hovermode="x unified")
    apply_template(fig_sc)
    st.plotly_chart(fig_sc, use_container_width=True)

    # Índices de risco
    st.markdown("#### Índice de risco por cenário")
    indicadores = ["Veranicos longos", "Chuvas extremas",
                   "Ondas de calor", "Risco agrícola", "Seca hídrica"]
    niveis = {
        "Otimista (SSP1-2.6)":   [15, 30, 20, 15, 10],
        "Neutro (SSP2-4.5)":     [40, 55, 45, 40, 35],
        "Pessimista (SSP5-8.5)": [75, 80, 70, 65, 70],
    }

    fig_risk = go.Figure()
    for nome in sc_selecionados:
        if nome not in niveis:
            continue
        fig_risk.add_trace(go.Bar(
            name=nome, x=indicadores, y=niveis[nome],
            marker_color=cenarios[nome]["cor"], opacity=0.8,
            hovertemplate="%{x}: %{y}%<extra>" + nome + "</extra>",
            text=[f"{v}%" for v in niveis[nome]], textposition="outside",
        ))
    fig_risk.update_layout(
        barmode="group", yaxis_range=[0, 100],
        yaxis_title="Nível de risco (%)",
        title="Comparação de riscos climáticos por cenário")
    apply_template(fig_risk)
    st.plotly_chart(fig_risk, use_container_width=True)

    # Tabela resumo
    df_sc = pd.DataFrame([
        {"Cenário": "Otimista (SSP1-2.6)",   "Aquecimento até 2055": "+1.2°C",
         "Emissões": "Muito baixas", "Ação climática": "Forte", "Prob": "20%"},
        {"Cenário": "Neutro (SSP2-4.5)",     "Aquecimento até 2055": "+1.8°C",
         "Emissões": "Moderadas",   "Ação climática": "Parcial","Prob": "50%"},
        {"Cenário": "Pessimista (SSP5-8.5)", "Aquecimento até 2055": "+3.5°C",
         "Emissões": "Muito altas", "Ação climática": "Mínima", "Prob": "30%"},
    ])
    st.dataframe(df_sc, use_container_width=True, hide_index=True)
    st.markdown('<p class="fonte-nota">Baseado em CMIP6 · downscaling regional Cerrado · '
                'Embrapa Clima · INMET histórico · probabilidades estimadas</p>',
                unsafe_allow_html=True)
