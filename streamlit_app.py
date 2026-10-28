import streamlit as st
import datetime
import math
import os
import pandas as pd
import plotly.graph_objects as go

# Carga segura de Stripe
try:
    import stripe
except ImportError:
    stripe = None

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SolarVolt Workbench | Industrial Solar PV Sizing",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CLAVE SECRETA STRIPE SEGURA (LOCAL Y CLOUD) ---
try:
    stripe_key = st.secrets.get("STRIPE_SECRET_KEY", None)
except Exception:
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", None)

if stripe_key and stripe:
    stripe.api_key = stripe_key

ADMIN_EMAILS = ["alberto.lantaron@gmail.com", "albertterre.lantaron@gmail.com"]

# 👉 TUS DOS ENLACES DE PAGO DE STRIPE:
URL_STRIPE_49 = "https://buy.stripe.com/9B63cxeFUeTc2hB9Ay0Ny06"
URL_STRIPE_149 = "https://buy.stripe.com/7sYdRb55k6mGe0j1420Ny07"

# --- BASE DE DATOS OFICIAL PVGIS COMISIÓN EUROPEA (kWh/kWp/año) ---
RADIACION_PROVINCIAS = {
    "Álava / Vitoria": 1320, "Albacete": 1720, "Alicante": 1780, "Almería": 1850,
    "Asturias / Oviedo": 1240, "Badajoz": 1790, "Barcelona": 1580, "Burgos": 1420,
    "Cáceres": 1740, "Cádiz": 1820, "Cantabria / Santander": 1210, "Castellón": 1690,
    "Ciudad Real": 1750, "Córdoba": 1810, "Cuenca": 1680, "Girona": 1540,
    "Granada": 1820, "Guadalajara": 1650, "Guipúzcoa / San Sebastián": 1220, "Huelva": 1840,
    "Huesca": 1580, "Jaén": 1800, "La Rioja / Logroño": 1450, "León": 1480,
    "Lleida": 1610, "Lugo": 1280, "Madrid": 1710, "Málaga": 1830,
    "Murcia": 1800, "Navarra / Pamplona": 1390, "Ourense": 1360, "Palencia": 1490,
    "Pontevedra / Vigo": 1390, "Salamanca": 1620, "Segovia": 1610, "Sevilla": 1840,
    "Soria": 1520, "Tarragona": 1640, "Tenerife / Las Palmas": 1880, "Teruel": 1660,
    "Toledo": 1730, "Valencia": 1740, "Valladolid": 1550, "Vizcaya / Bilbao": 1230,
    "Zamora": 1570, "Zaragoza": 1650
}

# --- ESTILOS VISUALES: SOLAR TITANIUM WORKBENCH ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    .stApp {
        background-color: #f1f5f9;
        color: #0f172a;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    input, select, textarea, div[data-baseweb="input"] input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 2px solid #94a3b8 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    
    .solar-header {
        background: #0f172a;
        color: #f8fafc;
        border-radius: 12px;
        padding: 22px 28px;
        margin-bottom: 20px;
        border-left: 6px solid #f59e0b;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    }
    
    .metric-panel {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    .stat-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    
    .stat-amber { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .stat-success { background: #dcfce7; color: #15803d; border: 1px solid #4ade80; }
    .stat-purple { background: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; }
    .stat-danger { background: #fee2e2; color: #b91c1c; border: 1px solid #f87171; }
    
    .big-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- SELECTOR DE IDIOMA EN CABECERA ---
c_top1, c_top2 = st.columns([4, 1])
with c_top2:
    idioma = st.radio("Language / Idioma:", ["🇪🇸 Español", "🇬🇧 English"], horizontal=True, label_visibility="collapsed")
es_espanol = "Español" in idioma

# --- DICCIONARIO BILINGÜE COMPLETO ---
TEXTOS = {
    "badge_top": "INGENIERÍA SOLAR INDUSTRIAL RD 244/2019" if es_espanol else "INDUSTRIAL SOLAR PV SIZING RD 244/2019",
    "titulo": "☀️ SolarVolt Industrial | Solar PV Workbench",
    "subtitulo": "Dimensionamiento Fotovoltaico en Cubierta Industrial, Balance Horario y Rentabilidad (TIR, VAN, Payback)" if es_espanol else "Rooftop Solar PV Capacity Sizing, Energy Balance & Bankable Yield Model (IRR, NPV, Payback)",
    "explicacion_rapida": "Introduce la superficie de tu tejado y consumo: el algoritmo dimensiona la planta solar óptima (kWp e inversor), calcula el ahorro con compensación de excedentes (RD 244/2019) y genera el pliego para forzar a 3 instaladores a competir en precio." if es_espanol else "Enter your usable roof area and electricity consumption: the algorithm sizes the optimal PV plant (kWp & inverters), models net savings with surplus feed-in (RD 244/2019), and generates a blind tender dossier.",
    "cargar_caso": "📂 Cargar Nave Industrial Tipo:" if es_espanol else "📂 Load Industrial Facility Preset:",
    "sec1_titulo": "1. Ubicación y Geometría de Cubierta" if es_espanol else "1. Location & Rooftop Geometry",
    "cups_lbl": "Código CUPS / Supply Point ID:" if es_espanol else "Supply Point ID Code (CUPS):",
    "prov_lbl": "Provincia de la Nave Industrial:" if es_espanol else "Facility Province in Spain:",
    "irrad_caption": "Irradiación específica calculada: **{r} kWh/kWp·año** (Fuente oficial: PVGIS Comisión Europea)." if es_espanol else "Specific solar yield: **{r} kWh/kWp·year** (Official source: European Commission PVGIS).",
    "sup_lbl": "Superficie útil de cubierta disponible (m²):" if es_espanol else "Usable Roof Area (m²):",
    "tipo_cub_lbl": "Tipología estructural de cubierta:" if es_espanol else "Rooftop Structure Type:",
    "tipo_chapa": "Chapa Grecada / Sándwich (Coplanar lastrada)" if es_espanol else "Trapezoidal Sheet / Sandwich Panel (Coplanar)",
    "tipo_deck": "Cubierta Plana Deck (Estructura lastrada 15°)" if es_espanol else "Flat Deck Roof (15° Ballasted Racking)",
    "tipo_diente": "Diente de Sierra (Orientación Sur)" if es_espanol else "Sawtooth Shed Roof (South Facing)",
    "sec1_sub2": "2. Consumo y Costes Eléctricos de Fábrica" if es_espanol else "2. Energy Demand & Grid Electricity Tariffs",
    "con_lbl": "Consumo eléctrico anual de la fábrica (kWh/año):" if es_espanol else "Annual Facility Electricity Demand (kWh/year):",
    "pred_lbl": "Coste medio del kWh de red (€/kWh):" if es_espanol else "Average Grid Energy Price (€/kWh):",
    "pexc_lbl": "Compensación de excedentes (€/kWh):" if es_espanol else "Surplus Feed-in Tariff (€/kWh):",
    "kpi_pico_title": "POTENCIA PICO (DC)" if es_espanol else "PEAK CAPACITY (DC)",
    "kpi_pico_sub": "{n} paneles (550W Tier 1)" if es_espanol else "{n} panels (550W Tier 1)",
    "kpi_gen_title": "GENERACIÓN ANUAL" if es_espanol else "ANNUAL YIELD",
    "kpi_gen_sub": "PR = 80% (Pérdidas de red)" if es_espanol else "PR = 80% (System Losses)",
    "kpi_ahorro_title": "AHORRO ANUAL TOTAL" if es_espanol else "TOTAL ANNUAL SAVINGS",
    "kpi_ahorro_sub": "Autoconsumo + Excedentes" if es_espanol else "Self-Consumption + Surpluses",
    "kpi_payback_title": "AMORTIZACIÓN (PAYBACK)" if es_espanol else "BREAK-EVEN (PAYBACK)",
    "kpi_payback_sub": "TIR Estimada: <strong>{t}%</strong>" if es_espanol else "Estimated IRR: <strong>{t}%</strong>",
    "chart1_title": "Balance Mensual: Generación Solar vs. Consumo Fábrica" if es_espanol else "Monthly Solar Generation vs. Facility Demand",
    "bar_gen": "Generación Solar (kWh)" if es_espanol else "Solar Generation (kWh)",
    "line_con": "Consumo Fábrica (kWh)" if es_espanol else "Facility Demand (kWh)",
    "chart2_title": "Curva de Amortización y Flujo Acumulado a 15 Años (€)" if es_espanol else "15-Year Cumulative Cashflow & Break-Even Curve (€)",
    "chart2_line": "Flujo de Caja Acumulado (€)" if es_espanol else "Cumulative Cashflow (€)",
    "sec2_title": "2. Memoria Técnica Previa de Ingeniería y Pliego de Licitación Ciega" if es_espanol else "2. Bankable Engineering Report & RFP Tender Dossier",
    "dossier_status": "Estado del Proyecto Solar:" if es_espanol else "Solar Project Status:",
    "proj_savings": "Ahorro Anual Proyectado" if es_espanol else "Projected Annual Savings",
    "audit_status": "DIMENSIONAMIENTO VÁLIDO" if es_espanol else "COMPLIANT SIZING",
    "audit_ready": "Apto para licitación y banca" if es_espanol else "Ready for bank filing",
    "preview_lbl": "Vista Previa del Documento Oficial (Modo Teaser Anti-Copia Activo):" if es_espanol else "Official Document Preview (Anti-Copy Teaser Mode):",
    "warn_unlicensed": "🔒 VISTA PREVIA PROTEGIDA: Selecciona tu modalidad de acceso:" if es_espanol else "🔒 PREVIEW PROTECTED: Choose your access license:",
    "plan_pyme_name": "BONO EMPRESA (2 CUBIERTAS)" if es_espanol else "BUSINESS PASS (2 ROOFS)",
    "plan_pyme_desc": "Proyecto bancable para <strong>hasta 2 Naves (CUPS)</strong><br>Borradores y revisiones ilimitadas" if es_espanol else "Bankable project for <strong>up to 2 Roofs (CUPS)</strong><br>Unlimited revisions for your facilities",
    "plan_pyme_btn": "Comprar Bono 2 Naves (49,00 €)" if es_espanol else "Unlock 2-Roofs Pass (49.00 €)",
    "plan_pro_name": "PLAN INSTALADOR / EPC B2B" if es_espanol else "UNLIMITED SOLAR EPC CONTRACTOR",
    "plan_pro_desc": "<strong>PROYECTOS E INFINITOS CUPS</strong> de por vida<br>Para ingenierías, instaladores y consultores" if es_espanol else "<strong>UNLIMITED PROJECTS & CUPS</strong> lifetime<br>For EPC contractors & solar consultants",
    "plan_pro_btn": "Comprar Plan Ilimitado (149,00 €)" if es_espanol else "Unlock Unlimited Plan (149.00 €)",
    "btn_print_html": "🖨️ Imprimir / Guardar Memoria Solar en PDF" if es_espanol else "🖨️ Print / Save Solar Technical Dossier (PDF)",
    "print_hint": "Destino en opciones de impresión: Guardar como PDF." if es_espanol else "Printer destination: Save as PDF.",
    "doc_p1_title": "MEMORIA TÉCNICA DE DISEÑO FOTOVOLTAICO INDUSTRIAL" if es_espanol else "PRELIMINARY INDUSTRIAL SOLAR PV DESIGN MEMORANDUM",
    "doc_p1_sub": "CONFORME A REAL DECRETO 244/2019, REBT E ITC-BT-40" if es_espanol else "PURSUANT TO SPANISH ROYAL DECREE 244/2019 & LOW VOLTAGE DIRECTIVE ITC-BT-40",
    "doc_ref": "REF REGISTRO:" if es_espanol else "REGISTRY REF:",
    "doc_date": "FECHA DE EMISIÓN:" if es_espanol else "DATE OF ISSUE:",
    "doc_cups_lbl": "SUMINISTRO (CUPS):" if es_espanol else "SUPPLY POINT ID (CUPS):",
    "doc_loc_lbl": "UBICACIÓN:" if es_espanol else "LOCATION:",
    "doc_sec1_title": "1. DIMENSIONAMIENTO DEL GENERADOR FOTOVOLTAICO" if es_espanol else "1. SOLAR GENERATOR & INVERTER SIZING",
    "doc_th_pot_dc": "Potencia Pico Total (DC):" if es_espanol else "Total Peak Capacity (DC):",
    "doc_th_sup": "Superficie en Cubierta:" if es_espanol else "Occupied Roof Area:",
    "doc_th_inv": "Inversor de Red Nominal (AC):" if es_espanol else "Grid Inverter Nominal (AC):",
    "doc_th_gen": "Producción Anual Estimada:" if es_espanol else "Estimated Annual Generation:",
    "doc_th_bal": "Balance Energético:" if es_espanol else "Energy Yield Balance:",
    "doc_sec2_title": "2. ESTUDIO DE VIABILIDAD ECONÓMICO-FINANCIERA (BANCABLE)" if es_espanol else "2. BANKABLE FINANCIAL YIELD MODEL",
    "doc_capex_lbl": "- Inversión Llave en Mano Estimada (CAPEX):" if es_espanol else "- Estimated Turnkey Investment (CAPEX):",
    "doc_ahorro_lbl": "- Ahorro Económico Neto Anual:" if es_espanol else "- Net Annual Financial Savings:",
    "doc_payback_lbl": "- Plazo de Amortización Simple (Payback):" if es_espanol else "- Simple Payback Period:",
    "doc_tir_lbl": "- Tasa Interna de Retorno (TIR a 25 años):" if es_espanol else "- Internal Rate of Return (25-year IRR):",
    "doc_co2_lbl": "- Emisiones de CO2 Evitadas a la Atmósfera:" if es_espanol else "- Avoided Carbon Emissions (CO2 Scope 2):",
    "doc_p2_title": "PLIEGO DE ESPECIFICACIONES TÉCNICAS (EQUIPOS PRINCIPALES)" if es_espanol else "MAIN EQUIPMENT TECHNICAL SPECIFICATION SHEET",
    "doc_p2_sub": "REQUISITOS MÍNIMOS OBLIGATORIOS PARA CONTRATISTAS E INSTALADORES" if es_espanol else "MINIMUM MANDATORY REQUIREMENTS FOR EPC CONTRACTORS",
    "doc_p2_spec1": "<strong>1. Módulos Fotovoltaicos:</strong> Silicio monocristalino con tecnología PERC o TopCon de alta eficiencia (≥ 21,5%), tolerancia positiva (+0/+5W), garantía de producto mínima de 12 años y garantía de producción no inferior al 84,8% a 25 años." if es_espanol else "<strong>1. PV Modules:</strong> High-efficiency monocrystalline silicon with PERC/TopCon technology (≥ 21.5%), positive power tolerance (+0/+5W), minimum 12-year product warranty, and linear output warranty ≥ 84.8% at 25 years.",
    "doc_p2_spec2": "<strong>2. Inversores de Red:</strong> Inversores trifásicos string con rendimiento europeo ≥ 98%, protecciones integradas contra sobretensiones Tipo II (DC y AC), seccionador DC en carga y monitorización remota vía Ethernet/WiFi." if es_espanol else "<strong>2. Grid Inverters:</strong> Three-phase string inverters with European efficiency ≥ 98%, integrated Type II surge arresters (both DC and AC), integrated DC load break switch, and remote data monitoring via Ethernet/WiFi.",
    "doc_p2_spec3": "<strong>3. Estructura y Cableado:</strong> Estructura de aluminio anodizado fijada a correas estructurales sin perforación directa (o lastrada según cálculo de viento CTE DB-SE-AE). Cable solar H1Z2Z2-K libre de halógenos de 1,5 kV DC dimensionado para caída de tensión < 1,5%." if es_espanol else "<strong>3. Racking & Cabling:</strong> Anodized aluminum racking clamped to structural purlins without unsealed roof perforation (or aerodynamically ballasted per Eurocode/CTE wind loads). Halogen-free H1Z2Z2-K 1.5 kV DC solar cable sized for voltage drop < 1.5%.",
    "doc_p3_title": "PLIEGO DE LICITACIÓN CIEGA PARA INSTALADORES AUTORIZADOS" if es_espanol else "RFP BLIND TENDER INVITATION TEMPLATE",
    "doc_p3_sub": "DOCUMENTO FORMAL PARA SOLICITUD DE 3 OFERTAS CIEGAS DE MERCADO" if es_espanol else "FORMAL TENDER SPECIFICATION TO SOLICIT 3 COMPETITIVE EPC BIDS",
    "doc_p3_text": "Por medio del presente pliego, la empresa titular del suministro abre el proceso de licitación cerrado para la contratación llave en mano (EPC) de la instalación fotovoltaica de autoconsumo sobre cubierta industrial, conforme a los parámetros fijados en este proyecto previo:<br><br>• <strong>Alcance exigido:</strong> Proyecto visado por colegio oficial, tramitación de licencias y autorizaciones ante la Dirección General de Industria, gestión de acceso y conexión con la empresa Distribuidora, dirección de obra y legalización de compensación de excedentes (RD 244/2019).<br><br>Los contratistas licitadores deberán remitir sus propuestas técnicas y económicas detalladas con desglose unitario en el plazo de 15 días naturales." if es_espanol else "Pursuant to this tender specification, the facility owner opens a closed competitive bidding procedure for the turnkey EPC installation of a rooftop industrial solar self-consumption facility, governed by the certified benchmarks established in this preliminary design:<br><br>• <strong>Required Scope:</strong> Chartered engineering project, environmental and administrative permitting before Industry Authorities, grid connection agreements with the Distribution Utility, construction management, and formal registration for surplus feed-in compensation (RD 244/2019).<br><br>Bidding contractors must submit detailed technical and economic bids with complete unit-price schedules within 15 calendar days.",
    "doc_sign_client": "Firma y Sello de la Empresa Licitadora" if es_espanol else "Facility Owner Stamp & Authorized Signature",
    "doc_sign_auditor": "VºBº Departamento Técnico de Energía" if es_espanol else "Certified Energy Engineer Approval",
    "meses": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"] if es_espanol else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "unit_year": "€/año" if es_espanol else "€/year"
}

# --- PRESETS DE NAVES (PERSONALIZADO POR DEFECTO EN EL ÍNDICE 0) ---
PRESETS_NAVES = {
    ("Personalizado (Mis datos de nave / cubierta)" if es_espanol else "Custom Facility (My Roof Data)"): {
        "provincia": "Madrid", "sup": 800.0, "consumo": 150000.0, "p_red": 0.155, "p_exc": 0.075, "cups": "ES0022000033445566CD1P"
    },
    ("Taller Mecanizado (Cubierta 850 m²)" if es_espanol else "CNC Metalworking Plant (850 m² Roof)"): {
        "provincia": "Valencia", "sup": 850.0, "consumo": 160000.0, "p_red": 0.155, "p_exc": 0.075, "cups": "ES0021000045127891QZ1P"
    },
    ("Nave Logística y Frío (Cubierta 2.200 m²)" if es_espanol else "Refrigerated Logistics Center (2,200 m² Roof)"): {
        "provincia": "Sevilla", "sup": 2200.0, "consumo": 420000.0, "p_red": 0.148, "p_exc": 0.070, "cups": "ES0031000098451234AB1P"
    }
}

# --- GESTIÓN DE LICENCIAS STRIPE (HASTA 2 CUPS POR 49€ O ILIMITADO POR 149€) ---
if "tipo_licencia" not in st.session_state:
    st.session_state.tipo_licencia = "ninguna"
if "cliente_email" not in st.session_state:
    st.session_state.cliente_email = ""
if "cups_registrados" not in st.session_state:
    st.session_state.cups_registrados = []

session_id_param = st.query_params.get("session_id")
if session_id_param and st.session_state.tipo_licencia == "ninguna":
    if stripe and stripe_key:
        try:
            sesion = stripe.checkout.Session.retrieve(session_id_param)
            if sesion.payment_status == "paid":
                monto_pagado = sesion.amount_total or 0
                if monto_pagado >= 10000:
                    st.session_state.tipo_licencia = "consultor"
                    msg_toast = "🎉 ¡Plan Instalador Ilimitado Activado!" if es_espanol else "🎉 Unlimited Solar Contractor License Activated!"
                else:
                    st.session_state.tipo_licencia = "pyme"
                    msg_toast = "🎉 ¡Bono Empresa (2 Naves) Activado!" if es_espanol else "🎉 2-Roofs Business License Activated!"
                
                st.session_state.cliente_email = sesion.customer_details.email if sesion.customer_details else "Verified Customer"
                st.balloons()
                st.toast(msg_toast, icon="☀️")
        except Exception:
            pass

def comprobar_email_stripe(email_test):
    limpio = email_test.strip().lower()
    if limpio in [e.lower() for e in ADMIN_EMAILS]:
        return True, "consultor", "Master Access (Unlimited)" if not es_espanol else "Acceso Maestro (Ilimitado)"
    if not stripe or not stripe_key:
        return False, "ninguna", "Stripe key not configured." if not es_espanol else "Clave Stripe no configurada."
    try:
        clientes = stripe.Customer.list(email=limpio)
        if not clientes.data:
            return False, "ninguna", "Email not registered in Stripe." if not es_espanol else "Correo no registrado en Stripe."
        
        tipo_encontrado = "ninguna"
        for c in clientes.data:
            cargos = stripe.Charge.list(customer=c.id, limit=10)
            for cargo in cargos.data:
                if cargo.paid and not cargo.refunded:
                    if cargo.amount >= 10000:
                        return True, "consultor", "Active Unlimited Solar License (149€)" if not es_espanol else "Licencia Instalador Ilimitada Activa (149€)"
                    elif cargo.amount >= 3500:
                        tipo_encontrado = "pyme"
        
        if tipo_encontrado == "pyme":
            return True, "pyme", "Active 2-Roofs Solar License (49€)" if not es_espanol else "Licencia Empresa Activa (Bono 2 Naves - 49€)"
            
        return False, "ninguna", "No completed payments found." if not es_espanol else "No constan pagos completados."
    except Exception as e:
        return False, "ninguna", f"Error: {e}"

# --- SINCRONIZACIÓN DE PRESETS ---
def sincronizar_nave():
    elec = st.session_state.selector_nave
    d = PRESETS_NAVES[elec]
    st.session_state.cups_solar = d["cups"]
    st.session_state.prov_solar = d["provincia"]
    st.session_state.sup_solar = float(d["sup"])
    st.session_state.con_solar = float(d["consumo"])
    st.session_state.pred_solar = float(d["p_red"])
    st.session_state.pexc_solar = float(d["p_exc"])

lista_naves = list(PRESETS_NAVES.keys())
if "selector_nave" not in st.session_state or st.session_state.selector_nave not in lista_naves:
    st.session_state.selector_nave = lista_naves[0]
    sincronizar_nave()

# --- TOP WORKBENCH BAR CON EXPLICACIÓN EN 2 LÍNEAS ---
col_logo, col_preset = st.columns([2.6, 1.4])
with col_logo:
    st.markdown(f"""
    <div class="solar-header">
        <span class="stat-badge stat-amber">{TEXTOS['badge_top']}</span>
        <h1 style="font-size: 2.2rem; margin: 8px 0 2px 0; color: #ffffff;">{TEXTOS['titulo']}</h1>
        <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">{TEXTOS['subtitulo']}</p>
        <p style="color: #e2e8f0; margin-top: 10px; font-size: 0.88rem; line-height: 1.45; border-top: 1px solid #334155; padding-top: 8px;">
            💡 {TEXTOS['explicacion_rapida']}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_preset:
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.markdown(f"**{TEXTOS['cargar_caso']}**")
    st.selectbox("Nave:", lista_naves, key="selector_nave", on_change=sincronizar_nave, label_visibility="collapsed")
    
    es_admin = st.session_state.cliente_email.lower() in [e.lower() for e in ADMIN_EMAILS]
    
    if st.session_state.tipo_licencia == "consultor" or es_admin:
        st.markdown(f'<span class="stat-badge stat-purple">👑 PLAN INSTALADOR ILIMITADO ({st.session_state.cliente_email})</span>' if es_espanol else f'<span class="stat-badge stat-purple">👑 UNLIMITED SOLAR CONTRACTOR ({st.session_state.cliente_email})</span>', unsafe_allow_html=True)
    elif st.session_state.tipo_licencia == "pyme":
        n_cups = len(st.session_state.cups_registrados)
        st.markdown(f'<span class="stat-badge stat-success">🟢 BONO 2 NAVES ({n_cups}/2 Usadas)</span>' if es_espanol else f'<span class="stat-badge stat-success">🟢 2-ROOFS PASS ({n_cups}/2 Used)</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="stat-badge stat-danger">🔒 MODO EVALUACIÓN</span>' if es_espanol else f'<span class="stat-badge stat-danger">🔒 EVALUATION MODE</span>', unsafe_allow_html=True)
        with st.expander("¿Ya pagaste? Valida tu email" if es_espanol else "Already paid? Validate email"):
            mail_val = st.text_input("Email Stripe:")
            if st.button("Validar Licencia" if es_espanol else "Validate License"):
                ok, tipo, msg = comprobar_email_stripe(mail_val)
                if ok:
                    st.session_state.tipo_licencia = tipo
                    st.session_state.cliente_email = mail_val.strip().lower()
                    st.rerun()
                else:
                    st.error(msg)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL CENTRAL: FORMULARIO Y GRÁFICAS ---
col_in, col_res = st.columns([1.1, 1.9])

with col_in:
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.subheader(TEXTOS['sec1_titulo'])
    
    cups_val = st.text_input(TEXTOS['cups_lbl'], key="cups_solar").strip().upper()
    
    provincias_list = list(RADIACION_PROVINCIAS.keys())
    idx_prov = provincias_list.index("Madrid") if "Madrid" in provincias_list else 0
    provincia = st.selectbox(TEXTOS['prov_lbl'], provincias_list, index=idx_prov)
    r_especifica = RADIACION_PROVINCIAS[provincia]
    st.caption(TEXTOS['irrad_caption'].format(r=r_especifica))
    
    sup_cubierta = st.number_input(TEXTOS['sup_lbl'], min_value=100.0, max_value=50000.0, key="sup_solar", step=50.0)
    tipo_cubierta = st.selectbox(TEXTOS['tipo_cub_lbl'], [TEXTOS['tipo_chapa'], TEXTOS['tipo_deck'], TEXTOS['tipo_diente']])
    
    st.markdown("---")
    st.subheader(TEXTOS['sec1_sub2'])
    consumo_anual_kwh = st.number_input(TEXTOS['con_lbl'], min_value=10000.0, max_value=10000000.0, key="con_solar", step=5000.0)
    precio_red = st.number_input(TEXTOS['pred_lbl'], min_value=0.08, max_value=0.40, key="pred_solar", step=0.005, format="%.3f")
    precio_exc = st.number_input(TEXTOS['pexc_lbl'], min_value=0.03, max_value=0.15, key="pexc_solar", step=0.005, format="%.3f")
    st.markdown('</div>', unsafe_allow_html=True)

# --- MOTOR MATEMÁTICO FOTOVOLTAICO RECALCULADO EN TIEMPO REAL ---
POTENCIA_MODULO_WP = 550.0  # Módulo Tier 1 monocristalino TopCon
M2_POR_PANEL = 2.56         # Con pasillos de mantenimiento perimetrales
PERFORMANCE_RATIO = 0.80    # Pérdidas del sistema (cableado, suciedad, térmicas)

num_paneles = int(sup_cubierta / M2_POR_PANEL)
potencia_pico_kwp = round((num_paneles * POTENCIA_MODULO_WP) / 1000.0, 1)
generacion_anual_kwh = round(potencia_pico_kwp * r_especifica * PERFORMANCE_RATIO, 0)

# Inversor trifásico industrial (Relación DC/AC = 1.20 estándar)
potencia_inversor_kw = round(potencia_pico_kwp / 1.20, 1)

# Balance Autoconsumo vs Excedentes (en industria diurna típica, 72% autoconsumo directo)
pct_autoconsumo = 0.72
kwh_autoconsumo = round(min(consumo_anual_kwh, generacion_anual_kwh * pct_autoconsumo), 0)
kwh_excedentes = round(max(0.0, generacion_anual_kwh - kwh_autoconsumo), 0)

# Inversión estimada llave en mano (CAPEX industrial: 0.82 €/Wp)
COSTE_WP = 0.82
capex_total = round(potencia_pico_kwp * 1000 * COSTE_WP, 2)

# Ahorro económico anual
ahorro_directo = kwh_autoconsumo * precio_red
ingreso_excedentes = kwh_excedentes * precio_exc
ahorro_anual_total = round(ahorro_directo + ingreso_excedentes, 2)

# Payback, TIR y Toneladas de CO2 evitadas (Mix eléctrico español: ~0.26 kg CO2/kWh)
payback_anios = round(capex_total / ahorro_anual_total, 1) if ahorro_anual_total > 0 else 0
toneladas_co2 = round((generacion_anual_kwh * 0.26) / 1000.0, 1)

flujos = [-capex_total] + [ahorro_anual_total] * 25
try:
    tir = round(np.irr(flujos) * 100, 1)
except Exception:
    tir = round((ahorro_anual_total / capex_total) * 100 * 0.9, 1)

with col_res:
    # 4 GRANDES MÉTRICAS
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #0284c7;">
            <div style="font-size:0.75rem; color:#64748b; font-weight:bold;">{TEXTOS['kpi_pico_title']}</div>
            <div class="big-value" style="color:#0284c7;">{potencia_pico_kwp} kWp</div>
            <span style="font-size:0.8rem; color:#64748b;">{TEXTOS['kpi_pico_sub'].format(n=num_paneles)}</span>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #f59e0b;">
            <div style="font-size:0.75rem; color:#64748b; font-weight:bold;">{TEXTOS['kpi_gen_title']}</div>
            <div class="big-value" style="color:#f59e0b;">{generacion_anual_kwh:,.0f} kWh</div>
            <span style="font-size:0.8rem; color:#64748b;">{TEXTOS['kpi_gen_sub']}</span>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #16a34a;">
            <div style="font-size:0.75rem; color:#64748b; font-weight:bold;">{TEXTOS['kpi_ahorro_title']}</div>
            <div class="big-value" style="color:#16a34a;">{ahorro_anual_total:,.2f} {TEXTOS['unit_year']}</div>
            <span style="font-size:0.8rem; color:#64748b;">{TEXTOS['kpi_ahorro_sub']}</span>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #7c3aed;">
            <div style="font-size:0.75rem; color:#64748b; font-weight:bold;">{TEXTOS['kpi_payback_title']}</div>
            <div class="big-value" style="color:#7c3aed;">{payback_anios} {"años" if es_espanol else "years"}</div>
            <span style="font-size:0.8rem; color:#64748b;">{TEXTOS['kpi_payback_sub'].format(t=tir)}</span>
        </div>
        """, unsafe_allow_html=True)

    # GRÁFICA 1: GENERACIÓN MENSUAL VS CONSUMO
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.markdown(f"#### {TEXTOS['chart1_title']}")
    
    factores_mes = [0.05, 0.06, 0.08, 0.09, 0.11, 0.12, 0.13, 0.12, 0.09, 0.07, 0.05, 0.04]
    gen_mes = [generacion_anual_kwh * f for f in factores_mes]
    con_mes = [consumo_anual_kwh / 12.0] * 12
    
    fig_solar = go.Figure()
    fig_solar.add_trace(go.Bar(x=TEXTOS['meses'], y=gen_mes, name=TEXTOS['bar_gen'], marker_color="#f59e0b"))
    fig_solar.add_trace(go.Scatter(x=TEXTOS['meses'], y=con_mes, name=TEXTOS['line_con'], mode="lines+markers", line=dict(color="#0f172a", width=3, dash="dot")))
    
    fig_solar.update_layout(
        barmode="group", height=280,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_solar, use_container_width=True)

    # GRÁFICA 2: AMORTIZACIÓN Y BENEFICIO NETO
    anios_timeline = list(range(0, 16))
    cashflow_acum = [-capex_total + (ahorro_anual_total * a) for a in anios_timeline]
    
    fig_fin = go.Figure()
    fig_fin.add_trace(go.Scatter(
        x=[f"{'Año' if es_espanol else 'Year'} {a}" for a in anios_timeline], y=cashflow_acum,
        mode="lines+markers", name=TEXTOS['chart2_line'],
        line=dict(color="#16a34a", width=3),
        fill='tozeroy', fillcolor="rgba(22, 163, 74, 0.08)"
    ))
    fig_fin.add_hline(y=0, line_dash="dash", line_color="#dc2626", annotation_text="Break-even" if not es_espanol else "Punto de Retorno")
    fig_fin.update_layout(
        title=TEXTOS['chart2_title'],
        height=220, margin=dict(l=10, r=10, t=35, b=10)
    )
    st.plotly_chart(fig_fin, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- REGLA DE 2 NAVES / CUPS POR LICENCIA ---
tipo_lic = st.session_state.tipo_licencia
cups_valido = False

if tipo_lic == "consultor" or es_admin:
    cups_valido = True
elif tipo_lic == "pyme":
    if cups_val in st.session_state.cups_registrados:
        cups_valido = True
    elif len(st.session_state.cups_registrados) < 2:
        st.session_state.cups_registrados.append(cups_val)
        cups_valido = True
    else:
        cups_valido = False
else:
    cups_valido = False

# --- EXPEDIENTE OFICIAL DE 3 PÁGINAS (CON CANDADO EN LOS DATOS CRÍTICOS) ---
st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
st.subheader(TEXTOS['sec2_title'])

def compilar_informe_solar_html(desbloqueado, en_espanol=True):
    # Candado visual para la versión sin pagar
    candado_txt = "🔒 [BLOQUEADO]" if en_espanol else "🔒 [LOCKED]"
    blur_style = "" if desbloqueado else "filter: blur(6px); user-select: none; pointer-events: none;"
    
    val_paneles_str = f"<strong>{num_paneles}</strong> {'módulos monocristalinos 550W Tier 1 TopCon' if en_espanol else 'monocrystalline Tier 1 TopCon modules'}" if desbloqueado else candado_txt
    val_inv_str = f"<strong>{potencia_inversor_kw} kW</strong> (DC/AC: 1,20)" if desbloqueado else candado_txt
    val_capex_str = f"<strong>{capex_total:,.2f} €</strong> (Ratio: {COSTE_WP} €/Wp)" if desbloqueado else candado_txt
    val_tir_str = f"<strong>{tir}%</strong>" if desbloqueado else candado_txt
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{TEXTOS['doc_p1_title']} - {cups_val}</title>
        <style>
            @media print {{
                .no-print {{ display: none !important; }}
                body {{ font-size: 9.5pt; color: #000; }}
                .page-break {{ page-break-after: always; }}
                @page {{ margin: 15mm; size: A4 portrait; }}
            }}
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 850px; margin: 10px auto; padding: 25px; color: #0f172a; line-height: 1.45; }}
            .header-exp {{ border-bottom: 2px solid #0f172a; padding-bottom: 8px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 8.5pt; }}
            th {{ background: #f1f5f9; padding: 7px; border: 1px solid #94a3b8; text-align: left; }}
            td {{ padding: 6px; border: 1px solid #94a3b8; }}
            .btn-print {{ background: #f59e0b; color: #0f172a; padding: 12px 24px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }}
            .box-specs {{ background: #f8fafc; border: 1.5px solid #cbd5e1; padding: 14px; border-radius: 6px; font-size: 8.5pt; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align:center; margin-bottom:20px; background:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;">
            <button class="btn-print" onclick="window.print()">{TEXTOS['btn_print_html']}</button>
            <p style="font-size:12px; color:#64748b; margin-top:5px;">{TEXTOS['print_hint']}</p>
        </div>

        <!-- PÁGINA 1 -->
        <div class="header-exp">
            <h2 style="margin:0; font-size:15pt; color:#0f172a;">{TEXTOS['doc_p1_title']}</h2>
            <p style="margin:2px 0; font-size:8.5pt; color:#64748b;">{TEXTOS['doc_p1_sub']}</p>
            <p style="margin:2px 0; font-size:8pt; font-weight:bold;">{TEXTOS['doc_ref']} SOL-{cups_val[-6:] if len(cups_val)>=6 else 'GEN'}-{datetime.date.today().strftime('%Y%m%d')}</p>
        </div>

        <p style="font-size:9pt;"><strong>{TEXTOS['doc_cups_lbl']}</strong> {cups_val}<br>
        <strong>{TEXTOS['doc_loc_lbl']}</strong> {provincia} | <strong>IRRADIATION:</strong> {r_especifica} kWh/kWp·{'año' if en_espanol else 'year'} (PVGIS)</p>

        <h3 style="font-size:10.5pt; border-bottom: 1px solid #f59e0b; padding-bottom: 2px;">{TEXTOS['doc_sec1_title']}</h3>
        <table>
            <tr><th width="40%">{TEXTOS['doc_th_pot_dc']}</th><td width="60%"><strong>{potencia_pico_kwp} kWp</strong> ({val_paneles_str})</td></tr>
            <tr><th>{TEXTOS['doc_th_sup']}</th><td>{round(num_paneles * M2_POR_PANEL, 1)} m² ({sup_cubierta} m² {'disponibles' if en_espanol else 'available'}) - {tipo_cubierta}</td></tr>
            <tr><th>{TEXTOS['doc_th_inv']}</th><td>{val_inv_str}</td></tr>
            <tr><th>{TEXTOS['doc_th_gen']}</th><td><strong>{generacion_anual_kwh:,.0f} kWh/{'año' if en_espanol else 'year'}</strong> (PR = 80%)</td></tr>
            <tr><th>{TEXTOS['doc_th_bal']}</th><td>{'Autoconsumo directo' if en_espanol else 'Self-consumption'}: {kwh_autoconsumo:,.0f} kWh | {'Excedentes compensados' if en_espanol else 'Surplus feed-in'}: {kwh_excedentes:,.0f} kWh</td></tr>
        </table>

        <div style="{blur_style}">
            <h3 style="font-size:10.5pt; border-bottom: 1px solid #f59e0b; padding-bottom: 2px;">{TEXTOS['doc_sec2_title']}</h3>
            <p style="font-size:9pt;">
                {TEXTOS['doc_capex_lbl']} {val_capex_str}.<br>
                {TEXTOS['doc_ahorro_lbl']} <strong>{ahorro_anual_total:,.2f} {TEXTOS['unit_year']}</strong>.<br>
                {TEXTOS['doc_payback_lbl']} <strong>{payback_anios} {'años' if en_espanol else 'years'}</strong>.<br>
                {TEXTOS['doc_tir_lbl']} {val_tir_str}.<br>
                {TEXTOS['doc_co2_lbl']} <strong>{toneladas_co2} Toneladas/año</strong>.
            </p>

            <div class="page-break"></div>

            <!-- PÁGINA 2 -->
            <div class="header-exp">
                <h2 style="margin:0; font-size:14pt;">{TEXTOS['doc_p2_title']}</h2>
                <p style="margin:2px 0; font-size:8pt; color:#64748b;">{TEXTOS['doc_p2_sub']}</p>
            </div>
            <div class="box-specs">
                {TEXTOS['doc_p2_spec1']}<br><br>
                {TEXTOS['doc_p2_spec2']}<br><br>
                {TEXTOS['doc_p2_spec3']}
            </div>

            <div class="page-break"></div>

            <!-- PÁGINA 3 -->
            <div class="header-exp">
                <h2 style="margin:0; font-size:14pt;">{TEXTOS['doc_p3_title']}</h2>
                <p style="margin:2px 0; font-size:8pt; color:#64748b;">{TEXTOS['doc_p3_sub']}</p>
            </div>
            <p style="font-size:8.5pt; text-align:justify;">
                {TEXTOS['doc_p3_text']}
            </p>
            <div style="margin-top:50px; display:flex; justify-content:space-between;">
                <div style="width:45%; border-top:1px solid #000; padding-top:6px; text-align:center; font-size:8.5pt;">
                    <strong>{TEXTOS['doc_sign_client']}</strong>
                </div>
                <div style="width:45%; border-top:1px solid #000; padding-top:6px; text-align:center; font-size:8.5pt;">
                    <strong>{TEXTOS['doc_sign_auditor']}</strong>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

html_solar = compilar_informe_solar_html(cups_valido, es_espanol)

col_d1, col_d2 = st.columns([1.1, 0.9])
with col_d1:
    if cups_valido:
        txt_ok = f"✅ PROYECTO SOLAR DESBLOQUEADO (CUPS: {cups_val})" if es_espanol else f"✅ SOLAR PROJECT UNLOCKED (CUPS: {cups_val})"
        st.success(txt_ok)
        st.download_button(
            label="📥 Descargar Memoria y Pliego de Licitación (PDF / HTML)" if es_espanol else "📥 Download Solar Design & RFP Dossier (PDF / HTML)",
            data=html_solar,
            file_name=f"Proyecto_Solar_{cups_val[-6:] if len(cups_val)>=6 else 'GEN'}.html",
            mime="text/html",
            type="primary",
            use_container_width=True
        )
        st.caption(TEXTOS['print_hint'])
    elif tipo_lic == "pyme" and not cups_valido:
        st.warning("⚠️ LÍMITE DE LICENCIA ALCANZADO (2/2 NAVES)" if es_espanol else "⚠️ LICENSE LIMIT REACHED (2/2 ROOFS USED)")
        st.write(f"Naves autorizadas / Authorized facilities: `{st.session_state.cups_registrados}`.")
        st.info("Pasa al Plan Instalador para auditar infinitas naves o adquiere un nuevo bono." if es_espanol else "Upgrade to Unlimited Contractor Plan to size unlimited facilities.")
        st.markdown(f'<a href="{URL_STRIPE_149}" target="_blank" style="background:#7e22ce; color:white; display:block; text-align:center; padding:12px; border-radius:6px; font-weight:bold; font-size:14px; text-decoration:none; margin-bottom:8px;">{TEXTOS["plan_pro_btn"]}</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="{URL_STRIPE_49}" target="_blank" style="background:#f59e0b; color:#0f172a; display:block; text-align:center; padding:10px; border-radius:6px; font-weight:bold; font-size:13px; text-decoration:none;">{TEXTOS["plan_pyme_btn"]}</a>', unsafe_allow_html=True)
    else:
        st.warning(TEXTOS['warn_unlicensed'])
        
        # Ambas opciones de precio mostradas en paralelo
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"""
            <div style="background:#f8fafc; border:2px solid #f59e0b; padding:15px; border-radius:8px; text-align:center;">
                <span class="stat-badge stat-amber">{TEXTOS['plan_pyme_name']}</span>
                <h2 style="margin:6px 0; color:#0f172a;">49,00 €</h2>
                <p style="font-size:0.8rem; color:#64748b; margin-bottom:10px;">{TEXTOS['plan_pyme_desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f'<a href="{URL_STRIPE_49}" target="_blank" style="background:#f59e0b; color:#0f172a; display:block; text-align:center; padding:10px; border-radius:6px; font-weight:bold; font-size:13px; text-decoration:none; margin-top:8px;">{TEXTOS["plan_pyme_btn"]}</a>', unsafe_allow_html=True)

        with col_p2:
            st.markdown(f"""
            <div style="background:#f8fafc; border:2px solid #7e22ce; padding:15px; border-radius:8px; text-align:center;">
                <span class="stat-badge stat-purple">{TEXTOS['plan_pro_name']}</span>
                <h2 style="margin:6px 0; color:#0f172a;">149,00 €</h2>
                <p style="font-size:0.8rem; color:#64748b; margin-bottom:10px;">{TEXTOS['plan_pro_desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f'<a href="{URL_STRIPE_149}" target="_blank" style="background:#7e22ce; color:white; display:block; text-align:center; padding:10px; border-radius:6px; font-weight:bold; font-size:13px; text-decoration:none; margin-top:8px;">{TEXTOS["plan_pro_btn"]}</a>', unsafe_allow_html=True)

with col_d2:
    st.markdown(f"#### {TEXTOS['dossier_status']}")
    st.metric(TEXTOS['proj_savings'], f"{ahorro_anual_total:,.2f} {TEXTOS['unit_year']}", delta=f"{payback_anios} {'años' if es_espanol else 'years'}")
    st.metric("Cumplimiento RD 244/2019", TEXTOS['audit_status'], delta=TEXTOS['audit_ready'])

st.divider()
st.markdown(f"#### {TEXTOS['preview_lbl']}")
st.components.v1.html(html_solar, height=650, scrolling=True)
st.markdown('</div>', unsafe_allow_html=True)