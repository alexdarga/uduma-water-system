import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

from utils.api_client import UdumaAPIClient
from utils.calculations import detect_anomalies
from components.charts import (
    create_consumption_chart,
    create_connection_type_pie,
    create_status_chart,
    create_revenue_chart
)
from components.javascript_components import render_leaflet_map

# Page configuration
st.set_page_config(
    page_title="Uduma Water Management System",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API client
api_client = UdumaAPIClient()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
    }
    .kpi-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .anomaly-alert {
        background-color: #ffcccc;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown('<h1 class="main-header">💧 Uduma Water Management System</h1>', unsafe_allow_html=True)

# Sidebar filters
st.sidebar.header("Filters")
commune_filter = st.sidebar.selectbox("Commune", ["All"] + ["Kita", "Sirakoro", "Pimperna", "Blendio"])
status_filter = st.sidebar.selectbox("Status", ["All", "active", "inactive", "maintenance"])
start_date = st.sidebar.date_input("Start Date", datetime(2024, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime(2024, 7, 31))

try:
    # Load data
    water_points = api_client.get_water_points() or []
    consumption_stats = api_client.get_consumption_stats(
        commune=commune_filter if commune_filter != "All" else None,
        status=status_filter if status_filter != "All" else None,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    ) or []
    kpis = api_client.get_kpis() or {}

    # Filter water points
    filtered_water_points = water_points
    if commune_filter != "All":
        filtered_water_points = [wp for wp in filtered_water_points if wp.get('commune') == commune_filter]
    if status_filter != "All":
        filtered_water_points = [wp for wp in filtered_water_points if wp.get('status') == status_filter]

    # --- KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><h3>{kpis.get("total_water_points", 0)}</h3><p>Total Water Points</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><h3>{kpis.get("active_water_points", 0)}</h3><p>Active Water Points</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><h3>{kpis.get("total_revenue", 0):,.0f}</h3><p>Total Revenue (FCFA)</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card"><h3>{kpis.get("anomalies_detected", 0)}</h3><p>Anomalies Detected</p></div>', unsafe_allow_html=True)

    # --- Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Consumption Analysis", "Geographic View", "Anomalies"])

    with tab1:
        st.header("Overview Dashboard")
        col1, col2 = st.columns(2)
        with col1:
            fig = create_connection_type_pie(filtered_water_points)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = create_status_chart(filtered_water_points)
            st.plotly_chart(fig, use_container_width=True)

        # Water points table
        st.subheader("Water Points")
        wp_df = pd.DataFrame(filtered_water_points)
        if not wp_df.empty:
            st.dataframe(wp_df[['name', 'commune', 'village', 'connection_type', 'status']])
        else:
            st.info("No water points match the selected filters.")

    with tab2:
        st.header("Consumption Analysis")
        stats_df = pd.DataFrame(consumption_stats)
        if not stats_df.empty:
            # Renommer colonnes pour uniformité
            if "total_consumption" in stats_df.columns:
                stats_df.rename(columns={"total_consumption": "consumption_m3"}, inplace=True)
            if "total_revenue" in stats_df.columns:
                stats_df.rename(columns={"total_revenue": "revenue_fcfa"}, inplace=True)

            if "month" in stats_df.columns:
                monthly_consumption = stats_df.groupby('month').agg({
                    "consumption_m3": "sum",
                    "revenue_fcfa": "sum"
                }).reset_index()
                # Renommer month -> month_name pour charts.py
                monthly_consumption = monthly_consumption.rename(columns={"month": "month_name"})

                col1, col2 = st.columns(2)
                with col1:
                    fig = create_consumption_chart(
                        monthly_consumption[['month_name', 'consumption_m3']],
                        chart_type="bar"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    fig = create_revenue_chart(
                        monthly_consumption[['month_name', 'revenue_fcfa']]
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Top performing points
                st.subheader("Top Performing Water Points")
                if "name" in stats_df.columns and "revenue_fcfa" in stats_df.columns:
                    top_points = stats_df.groupby('name').agg({
                        'consumption_m3': 'sum',
                        'revenue_fcfa': 'sum'
                    }).nlargest(5, 'revenue_fcfa').reset_index()
                    st.dataframe(top_points)
            else:
                st.info("No valid consumption data available for the selected filters.")
        else:
            st.info("No consumption data available for the selected filters.")

    with tab3:
        st.header("Geographic Distribution")
        render_leaflet_map(filtered_water_points)

    with tab4:
        st.header("Anomaly Detection")
        all_readings = []
        for wp in filtered_water_points:
            try:
                readings = api_client.get_water_point_consumption(wp.get('id'))
                for reading in readings:
                    reading['water_point_id'] = wp.get('id')
                    reading['water_point_name'] = wp.get('name')
                all_readings.extend(readings)
            except Exception:
                continue

        anomalies = detect_anomalies(all_readings)
        if anomalies:
            st.warning(f"🚨 {len(anomalies)} anomalies detected!")
            for anomaly in anomalies:
                st.markdown(f"""
                <div class="anomaly-alert">
                    <strong>{anomaly['type'].replace('_', ' ').title()}</strong><br>
                    Water Point: {anomaly.get('water_point_name', 'Unknown')}<br>
                    Date: {anomaly['date']}<br>
                    {anomaly['message']}
                </div>
                """, unsafe_allow_html=True)
                st.write("---")
        else:
            st.success("✅ No anomalies detected in the selected data!")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure the FastAPI server is running on http://localhost:8000")

# Footer
st.markdown("---")
st.markdown("**Uduma Water Management System** - Built with FastAPI & Streamlit")