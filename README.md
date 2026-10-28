# ☀️ SolarVolt Industrial | Rooftop Solar PV Sizing & Tender SaaS

[![Streamlit App](https://static.streamlit.io/badge/streamlit_badge_black_white.svg)](https://solarvolt.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)

B2B industrial engineering platform designed to mathematically size rooftop solar photovoltaic plants, simulate daytime self-consumption vs surplus compensation, and generate bankable financial models (IRR, NPV, Payback) and blind tender RFPs under **Spanish Royal Decree 244/2019**.

👉 **Live Production URL:** [https://solarvolt.streamlit.app](https://solarvolt.streamlit.app)

---

## 🏭 Industrial Problem Solved
When industrial facilities evaluate installing rooftop solar panels, they face two critical issues:
1. **Oversized and Inflated Quotes:** Without independent preliminary engineering, contractors routinely oversize installations and charge 20% to 30% above market rates.
2. **Bank Financing Roadblocks:** Banks and green funds require certified financial yield schedules (IRR, NPV, Break-even) and official irradiation data before approving financing.

## ⚡ Technical Features
- **Official EU PVGIS Integration:** Specific solar irradiation metrics for all 50 Spanish provinces.
- **Industrial PV Generator Sizing:** Optimizes Tier 1 550Wp modules and three-phase inverters (1.20 DC/AC ratio).
- **Hourly Self-Consumption & Surplus Balance:** Calculates daytime manufacturing load vs grid compensation under RD 244/2019.
- **3-Page Bankable Memorandum & Blind Tender RFP:** Technical equipment specifications, financial yield models, and formal tender document ready to solicit 3 competitive EPC quotes.
- **100% Strict Bilingual Support:** Full Spanish (`🇪🇸 ES`) and English (`🇬🇧 EN`) interface and official PDF reports.

## 🛠️ Tech Stack
- **Engine:** Python 3.10+, Pandas, NumPy
- **Interface:** Streamlit (Titanium SCADA Workbench)
- **Data Visualization:** Plotly Graph Objects
- **Billing API:** Stripe Python SDK

---
Developed by **Alberto Lantarón**  
*Industrial Engineering & Applied Software Solutions*
