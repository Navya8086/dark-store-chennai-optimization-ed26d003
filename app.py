"""
app.py - Streamlit Web Application
Dark Store Location Optimization Engine (Chennai City Quick-Commerce)
Assignment 1: Distance-Constrained Facility Location Optimization
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium

from geo_data import (
    CHENNAI_BOUNDS,
    get_candidate_stores,
    generate_customers,
)
from optimizer import solve_dark_store_optimization, run_k_benchmark

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dark Store Location Optimizer | Chennai",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Custom Styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .kpi-title {
        font-size: 0.85rem;
        color: #6c757d;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #212529;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #28a745;
        margin-top: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python-Dark.svg",
        width=50,
    )
    st.title("⚙️ Control Panel")
    st.markdown("Configure scenario parameters for Chennai network optimization.")
    
    st.subheader("📍 Network Geography")
    candidate_count = st.slider(
        "Candidate Dark Stores (M)",
        min_value=5,
        max_value=50,
        value=50,
        step=5,
        help="Number of candidate store hubs in Chennai (up to 50 curated locations).",
    )
    
    customer_count = st.slider(
        "Customer Count (N)",
        min_value=100,
        max_value=10000,
        value=2000,
        step=100,
        help="Number of customers across Chennai. (Use 10,000 for the full assignment benchmark).",
    )
    
    max_stores_k = st.slider(
        "Max Allowed Open Stores (K)",
        min_value=1,
        max_value=candidate_count,
        value=min(10, candidate_count),
        step=1,
        help="Budget / operational limit on the total number of dark stores that can be opened.",
    )
    
    st.subheader("⏱️ Service Guarantee")
    d_max_km = st.slider(
        "Max Allowed Distance (D_max in km)",
        min_value=1.0,
        max_value=10.0,
        value=3.0,
        step=0.5,
        help="Assignment enhancement: Dark stores are strictly forbidden from serving customers beyond this radius (10-minute delivery guarantee).",
    )
    
    with st.expander("💰 Economic & Operating Assumptions", expanded=False):
        revenue_per_order = st.number_input(
            "Revenue Margin per Order (₹)",
            min_value=10.0,
            max_value=500.0,
            value=120.0,
            step=5.0,
            help="Gross revenue earned per fulfilled customer order.",
        )
        delivery_cost_per_km = st.number_input(
            "Delivery Cost per km (₹)",
            min_value=1.0,
            max_value=50.0,
            value=15.0,
            step=1.0,
            help="Variable delivery transit cost per kilometer traveled.",
        )
        fixed_cost_per_store = st.number_input(
            "Fixed Daily Cost per Store (₹)",
            min_value=1000.0,
            max_value=50000.0,
            value=10000.0,
            step=500.0,
            help="Fixed daily lease, staffing, utilities, and tech overhead to operate an open dark store.",
        )
        store_capacity = st.number_input(
            "Store Capacity (orders/day)",
            min_value=100,
            max_value=10000,
            value=2000,
            step=100,
            help="Maximum dispatch capacity per dark store per day.",
        )
        circuity_factor = st.number_input(
            "Road Circuity Factor",
            min_value=1.0,
            max_value=1.8,
            value=1.25,
            step=0.05,
            help="Urban road multiplier applied to Haversine great-circle distance (standard = 1.25).",
        )
        random_seed = st.number_input(
            "Customer Random Seed",
            min_value=1,
            max_value=99999,
            value=42,
            step=1,
        )

    st.markdown("---")
    run_btn = st.button("🚀 Run Optimization", type="primary", use_container_width=True)

# ---------------------------------------------------------
# App Header
# ---------------------------------------------------------
st.title("⚡ Dark Store Location Optimization")
st.markdown(
    """
    **Mixed-Integer Linear Programming (MILP) Model with Maximum Delivery Distance Constraint ($D_{max}$)**  
    *Optimizing quick-commerce 10-minute micro-warehouse placement across Greater Chennai Metropolitan Area.*
    """
)

# ---------------------------------------------------------
# Tabs: 1) Interactive Solution & Map, 2) Benchmark Sensitivity Analysis, 3) Model Formulation
# ---------------------------------------------------------
tab_map, tab_benchmark, tab_formulation = st.tabs([
    "📍 Interactive Solution & Map",
    "📈 10,000 Customers Benchmark (K ∈ [2, 5, 10, 20, 25])",
    "📐 Mathematical Model & Formulas",
])

# ---------------------------------------------------------
# Data Caching & Helper Functions
# ---------------------------------------------------------
@st.cache_data
def get_cached_data(cand_count: int, cust_count: int, seed: int):
    stores = get_candidate_stores(cand_count)
    customers = generate_customers(cust_count, stores, random_seed=seed)
    return stores, customers


@st.cache_data
def get_cached_solution(cand_count, cust_count, k_val, d_max, rev, del_cost, fix_cost, cap, circuity, seed):
    stores = get_candidate_stores(cand_count)
    customers = generate_customers(cust_count, stores, random_seed=seed)
    return solve_dark_store_optimization(
        customers_df=customers,
        stores_df=stores,
        d_max_km=d_max,
        max_stores_allowed_k=k_val,
        revenue_per_order=rev,
        delivery_cost_per_km=del_cost,
        fixed_cost_per_store=fix_cost,
        store_capacity=cap,
        circuity_factor=circuity,
    )


# ---------------------------------------------------------
# Tab 1: Interactive Solution & Map
# ---------------------------------------------------------
with tab_map:
    # Run optimization (or use cached default)
    solution = get_cached_solution(
        candidate_count, customer_count, max_stores_k, d_max_km,
        revenue_per_order, delivery_cost_per_km, fixed_cost_per_store,
        store_capacity, circuity_factor, random_seed
    )
    
    kpis = solution["kpis"]
    store_results = solution["store_results"]
    assignments = solution["assignments"]
    unserved = solution["unserved_customers"]
    
    # -----------------------------------------------------
    # Executive KPI Cards
    # -----------------------------------------------------
    st.subheader("1. Executive KPIs")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="Net Daily Profit",
            value=f"₹{kpis['net_profit']:,.2f}",
            delta=f"Revenue: ₹{kpis['total_revenue']:,.0f}",
        )
    with c2:
        st.metric(
            label="Demand Fulfilled",
            value=f"{kpis['demand_fulfilled']:,} / {kpis['total_demand']:,}",
            delta=f"{kpis['fulfillment_rate_pct']:.1f}% fulfillment",
        )
    with c3:
        st.metric(
            label="Dark Stores Opened",
            value=f"{kpis['stores_opened']} / {candidate_count}",
            delta=f"Limit (K) = {kpis['max_stores_allowed_k']}",
        )
    with c4:
        st.metric(
            label="Avg Delivery Distance",
            value=f"{kpis['avg_delivery_distance_km']:.2f} km",
            delta=f"Max Allowed = {d_max_km:.1f} km",
        )
        
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric(label="Total Revenue", value=f"₹{kpis['total_revenue']:,.2f}")
    with c6:
        st.metric(label="Delivery Costs", value=f"₹{kpis['total_delivery_cost']:,.2f}")
    with c7:
        st.metric(label="Store Fixed Costs", value=f"₹{kpis['total_fixed_cost']:,.2f}")
    with c8:
        st.metric(
            label="MIP Solver Execution",
            value=f"{kpis['solve_duration_sec']:.2f} s",
            delta=f"{kpis['sparse_variable_count']:,} active vars ({kpis['solver_status']})",
        )
        
    st.markdown("---")
    
    # -----------------------------------------------------
    # KPI Table: Detailed Store-Level Solution
    # -----------------------------------------------------
    st.subheader("2. Dark Store Operational Breakdown (KPI Table)")
    
    col_filter1, col_filter2 = st.columns([2, 1])
    with col_filter1:
        filter_status = st.radio(
            "Show Stores:",
            ["Opened Only", "All Candidate Stores", "Closed Only"],
            horizontal=True,
        )
    with col_filter2:
        st.caption("Sortable operational summary table with financial contributions per location.")
        
    if filter_status == "Opened Only":
        display_stores = store_results[store_results["Is Opened"] == True]
    elif filter_status == "Closed Only":
        display_stores = store_results[store_results["Is Opened"] == False]
    else:
        display_stores = store_results
        
    st.dataframe(
        display_stores[[
            "Store ID", "Name", "Zone", "Status", "Orders Fulfilled",
            "Capacity", "Capacity Utilization (%)", "Revenue (₹)",
            "Delivery Cost (₹)", "Fixed Cost (₹)", "Net Profit Contribution (₹)"
        ]],
        use_container_width=True,
        hide_index=True,
    )
    
    st.markdown("---")
    
    # -----------------------------------------------------
    # Section 2: Detailed Solution on an Interactive Map
    # -----------------------------------------------------
    st.subheader("3. Detailed Solution on Interactive Chennai Map")
    st.markdown(
        f"""
        - 🟢 **Opened Dark Stores**: Marked with green icons.
        - ⚪ **Closed Candidates**: Marked with gray dots.
        - ⭕ **Dashed Circle**: Maximum allowable delivery radius ($D_{{max}} = {d_max_km}$ km).
        - 🔵 **Sample Fulfilled Customers**: Blue dots with sample delivery paths to their assigned store.
        - 🔴 **Sample Unfulfilled Customers**: Red dots (outside coverage or store capacity limits).
        """
    )
    
    # Map controls
    map_c1, map_c2 = st.columns([1, 1])
    with map_c1:
        sample_customers_count = st.slider(
            "Customer Points to Render on Map (Sampling for high responsiveness)",
            min_value=50,
            max_value=min(1000, customer_count),
            value=min(300, customer_count),
            step=50,
        )
    with map_c2:
        show_delivery_lines = st.checkbox("Show delivery lines to assigned stores", value=True)
        
    # Build Folium Map
    chennai_map = folium.Map(
        location=[CHENNAI_BOUNDS["center_lat"], CHENNAI_BOUNDS["center_lon"]],
        zoom_start=11,
        tiles="CartoDB positron",
    )
    
    # Add opened and candidate stores
    for _, store in store_results.iterrows():
        is_opened = store["Is Opened"]
        lat, lon = store["Latitude"], store["Longitude"]
        name = store["Name"]
        zone = store["Zone"]
        orders = store["Orders Fulfilled"]
        profit_contrib = store["Net Profit Contribution (₹)"]
        util = store["Capacity Utilization (%)"]
        
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
            <b>{name}</b><br/>
            <i>Zone: {zone}</i><br/>
            <b>Status:</b> {'<span style="color:green;font-weight:bold;">OPENED</span>' if is_opened else '<span style="color:gray;">CLOSED</span>'}<br/>
            <b>Orders Served:</b> {orders:,} / {store['Capacity']:,} ({util}%)<br/>
            <b>Net Contribution:</b> ₹{profit_contrib:,.2f}<br/>
            <b>Coverage Radius:</b> {d_max_km} km
        </div>
        """
        
        if is_opened:
            # Green store marker
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"🏪 OPENED: {name} ({orders} orders)",
                icon=folium.Icon(color="green", icon="shopping-cart", prefix="fa"),
            ).add_to(chennai_map)
            
            # Coverage radius circle
            folium.Circle(
                location=[lat, lon],
                radius=float(d_max_km * 1000),  # meters
                color="#28a745",
                weight=1.5,
                fill=True,
                fill_color="#28a745",
                fill_opacity=0.08,
                dash_array="6, 6",
            ).add_to(chennai_map)
        else:
            # Gray candidate marker
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"⚪ Candidate (Closed): {name}",
                color="#6c757d",
                fill=True,
                fill_color="#adb5bd",
                fill_opacity=0.7,
            ).add_to(chennai_map)
            
    # Sample fulfilled customers
    if not assignments.empty and sample_customers_count > 0:
        sample_assignments = assignments.sample(
            n=min(sample_customers_count, len(assignments)),
            random_state=42,
        )
        
        for _, row in sample_assignments.iterrows():
            c_lat, c_lon = row["customer_lat"], row["customer_lon"]
            s_lat, s_lon = row["store_lat"], row["store_lon"]
            dist = row["distance_km"]
            s_name = row["store_name"]
            
            # Customer marker
            folium.CircleMarker(
                location=[c_lat, c_lon],
                radius=3,
                color="#007bff",
                fill=True,
                fill_color="#007bff",
                fill_opacity=0.8,
                tooltip=f"Cust #{row['customer_id']} -> {s_name} ({dist} km)",
            ).add_to(chennai_map)
            
            # Connection line
            if show_delivery_lines:
                folium.PolyLine(
                    locations=[[c_lat, c_lon], [s_lat, s_lon]],
                    color="#007bff",
                    weight=1.0,
                    opacity=0.35,
                ).add_to(chennai_map)
                
    # Sample unserved customers
    if not unserved.empty:
        sample_unserved = unserved.sample(
            n=min(int(sample_customers_count * 0.25), len(unserved)),
            random_state=42,
        )
        for _, row in sample_unserved.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=2.5,
                color="#dc3545",
                fill=True,
                fill_color="#dc3545",
                fill_opacity=0.6,
                tooltip=f"Unserved Cust #{int(row['id'])} (Beyond {d_max_km}km or capacity cap)",
            ).add_to(chennai_map)
            
    # Render map
    st_folium(chennai_map, width="100%", height=550)


# ---------------------------------------------------------
# Tab 2: Assignment Benchmark (10,000 Customers vs 50 Candidates)
# ---------------------------------------------------------
with tab_benchmark:
    st.header("📈 Assignment 1 Benchmark Sensitivity Analysis")
    st.markdown(
        """
        > **Mandate from Problem Statement:**  
        > *For 10,000 customers and 50 dark store location options, plot the profit when up to at most 2, 5, 10, 20, 25 dark store locations are allowed to open.*
        """
    )
    
    col_bench_info, col_bench_action = st.columns([3, 1])
    with col_bench_info:
        st.info(
            f"""
            **Benchmark Setup:**
            - Customers: **10,000**
            - Dark Store Candidates: **50**
            - Maximum Distance ($D_{{max}}$): **{d_max_km} km**
            - Max Stores Allowed ($K$): **[2, 5, 10, 20, 25]**
            - Revenue per Order: **₹{revenue_per_order}** | Delivery Cost: **₹{delivery_cost_per_km}/km** | Store Fixed Cost: **₹{fixed_cost_per_store}/day**
            """
        )
    with col_bench_action:
        run_bench_btn = st.button(
            "⚡ Compute Full Benchmark",
            type="primary",
            use_container_width=True,
            help="Solves all 5 optimization models for 10,000 customers using spatial pre-filtering.",
        )
        
    @st.cache_data
    def compute_benchmark_live(d_max, rev, del_cost, fix_cost, cap, circuity, seed):
        stores_50 = get_candidate_stores(50)
        customers_10k = generate_customers(10000, stores_50, random_seed=seed)
        k_list = [2, 5, 10, 20, 25]
        return run_k_benchmark(
            customers_df=customers_10k,
            stores_df=stores_50,
            k_values=k_list,
            d_max_km=d_max,
            revenue_per_order=rev,
            delivery_cost_per_km=del_cost,
            fixed_cost_per_store=fix_cost,
            store_capacity=cap,
            circuity_factor=circuity,
        )

    # Check if standard baseline parameters match precomputed benchmark
    is_standard_baseline = (
        abs(d_max_km - 3.0) < 1e-4
        and abs(revenue_per_order - 120.0) < 1e-4
        and abs(delivery_cost_per_km - 15.0) < 1e-4
        and abs(fixed_cost_per_store - 10000.0) < 1e-4
        and store_capacity == 2000
        and abs(circuity_factor - 1.25) < 1e-4
        and random_seed == 42
    )

    import os
    default_csv_path = os.path.join(os.path.dirname(__file__), "benchmark_10k_default.csv")

    if run_bench_btn:
        with st.spinner("⚡ Solving MIP optimization across K ∈ [2, 5, 10, 20, 25] for 10,000 customers..."):
            benchmark_df = compute_benchmark_live(
                d_max_km, revenue_per_order, delivery_cost_per_km, fixed_cost_per_store,
                store_capacity, circuity_factor, random_seed
            )
            st.success("✅ Real-time benchmark re-computation complete!")
    elif is_standard_baseline and os.path.exists(default_csv_path):
        benchmark_df = pd.read_csv(default_csv_path)
    else:
        with st.spinner("⚡ Solving MIP optimization across K ∈ [2, 5, 10, 20, 25] for 10,000 customers..."):
            benchmark_df = compute_benchmark_live(
                d_max_km, revenue_per_order, delivery_cost_per_km, fixed_cost_per_store,
                store_capacity, circuity_factor, random_seed
            )
    
    st.subheader("Comparison Table: Sensitivity Analysis ($K \\in \\{2, 5, 10, 20, 25\\}$)")
    st.dataframe(
        benchmark_df.style.format({
            "Net Profit (₹)": "₹{:,.2f}",
            "Total Revenue (₹)": "₹{:,.2f}",
            "Total Delivery Cost (₹)": "₹{:,.2f}",
            "Fixed Operating Cost (₹)": "₹{:,.2f}",
            "Demand Fulfilled (Orders)": "{:,}",
            "Fulfillment Rate (%)": "{:.2f}%",
            "Avg Distance (km)": "{:.2f} km",
            "Solve Time (s)": "{:.2f} s",
        }),
        use_container_width=True,
        hide_index=True,
    )
    
    st.markdown("---")
    st.subheader("Dual-Axis Visualization: Profit, Costs & Demand Fulfillment")
    
    # Plotly dual-axis chart
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
    )
    
    # Net Profit Bar
    fig.add_trace(
        go.Bar(
            x=benchmark_df["Max Stores Allowed (K)"].astype(str),
            y=benchmark_df["Net Profit (₹)"],
            name="Net Profit (₹)",
            marker_color="#2ca02c",
            text=[f"₹{val:,.0f}" for val in benchmark_df["Net Profit (₹)"]],
            textposition="auto",
        ),
        secondary_y=False,
    )
    
    # Total Revenue Line
    fig.add_trace(
        go.Scatter(
            x=benchmark_df["Max Stores Allowed (K)"].astype(str),
            y=benchmark_df["Total Revenue (₹)"],
            name="Total Revenue (₹)",
            mode="lines+markers",
            line=dict(color="#1f77b4", width=3),
        ),
        secondary_y=False,
    )
    
    # Total Fixed Cost Line
    fig.add_trace(
        go.Scatter(
            x=benchmark_df["Max Stores Allowed (K)"].astype(str),
            y=benchmark_df["Fixed Operating Cost (₹)"],
            name="Fixed Store Costs (₹)",
            mode="lines+markers",
            line=dict(color="#d62728", width=2, dash="dash"),
        ),
        secondary_y=False,
    )
    
    # Delivery Cost Line
    fig.add_trace(
        go.Scatter(
            x=benchmark_df["Max Stores Allowed (K)"].astype(str),
            y=benchmark_df["Total Delivery Cost (₹)"],
            name="Delivery Costs (₹)",
            mode="lines+markers",
            line=dict(color="#ff7f0e", width=2, dash="dot"),
        ),
        secondary_y=False,
    )
    
    # Fulfillment Rate Line (Secondary Y-Axis)
    fig.add_trace(
        go.Scatter(
            x=benchmark_df["Max Stores Allowed (K)"].astype(str),
            y=benchmark_df["Fulfillment Rate (%)"],
            name="Demand Fulfilled (%)",
            mode="lines+markers+text",
            line=dict(color="#9467bd", width=3),
            text=[f"{val:.1f}%" for val in benchmark_df["Fulfillment Rate (%)"]],
            textposition="top center",
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        title="<b>Impact of Store Count (K) on Profitability and Customer Coverage</b>",
        xaxis_title="<b>Maximum Dark Stores Allowed to Open (K)</b>",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        height=520,
    )
    fig.update_yaxes(title_text="<b>Financials (₹)</b>", secondary_y=False, showgrid=True)
    fig.update_yaxes(title_text="<b>Fulfillment Rate (%)</b>", secondary_y=True, showgrid=False, range=[0, 105])
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Business Takeaways & Diminishing Returns Analysis
    st.subheader("💡 Business Insights & Diminishing Returns Analysis")
    
    best_row = benchmark_df.loc[benchmark_df["Net Profit (₹)"].idxmax()]
    k_best = int(best_row["Max Stores Allowed (K)"])
    max_prof = best_row["Net Profit (₹)"]
    best_rate = best_row["Fulfillment Rate (%)"]
    
    st.markdown(
        f"""
        1. **Optimal Profit Sweet Spot**:
           Opening **K = {k_best} stores** yields the highest net daily profit of **₹{max_prof:,.2f}** with **{best_rate:.1f}%** demand coverage.
        2. **Diminishing Marginal Returns**:
           As $K$ increases from 2 to 10, each newly opened store captures unserved high-density clusters, delivering high marginal revenue well above the ₹10,000 fixed daily store cost.
        3. **The Cannibalization & Fixed Cost Crossover**:
           Beyond $K = 20$, newly opened stores begin competing for customers in overlapping $D_{{max}}$ radii or cover lower-density fringe areas. The additional order revenue no longer covers the ₹10,000 fixed daily store cost, causing net profit to plateau or decrease.
        """
    )


# ---------------------------------------------------------
# Tab 3: Mathematical Model & Formulas
# ---------------------------------------------------------
with tab_formulation:
    st.header("📐 Mathematical Formulation (Mixed-Integer Linear Programming)")
    st.markdown(
        """
        The dark store location optimization problem is modeled as a **Capacitated Facility Location Problem with Service Distance Cutoff (CFLP-Dmax)**.
        """
    )
    
    st.subheader("1. Sets and Indices")
    st.markdown(
        r"""
        - $I = \{1, 2, \dots, N\}$: Set of customer locations (e.g., $N = 10,000$).
        - $J = \{1, 2, \dots, M\}$: Set of candidate dark store locations (e.g., $M = 50$).
        """
    )
    
    st.subheader("2. Parameters")
    st.markdown(
        r"""
        - $d_{ij}$: Road delivery distance between store $j$ and customer $i$ ($km$), computed via Haversine formula with urban circuity factor ($\gamma = 1.25$).
        - $D_{\max}$: Maximum allowable service distance (e.g., $3.0\text{ km}$, guaranteeing 10-minute delivery).
        - $Demand_i$: Order demand from customer $i$ (1 order).
        - $Capacity_j$: Maximum orders store $j$ can fulfill per day (e.g., $2,000\text{ orders}$).
        - $FixCost_j$: Fixed daily operating cost to open candidate store $j$ (e.g., ₹$10,000$).
        - $DelCostPerKm$: Variable delivery cost per km (e.g., ₹$15/\text{km}$).
          $$\text{Delivery Cost } c_{ij} = DelCostPerKm \times d_{ij}$$
        - $RevenuePerOrder$: Revenue margin earned per order fulfilled (e.g., ₹$120$).
        - $K$: Maximum number of stores permitted to open ($K \in \{2, 5, 10, 20, 25\}$).
        """
    )
    
    st.subheader("3. Decision Variables")
    st.markdown(
        r"""
        - $y_j \in \{0, 1\}$: Binary store opening decision:
          $$y_j = \begin{cases} 1 & \text{if candidate store } j \text{ is opened} \\ 0 & \text{otherwise} \end{cases}$$
        - $x_{ij} \in [0, 1]$: Order fulfillment variable:
          $$x_{ij} = \text{fraction of customer } i\text{'s order served from store } j$$
        """
    )
    
    st.subheader("4. Objective Function")
    st.markdown(
        r"""
        $$\max \text{Net Profit} = \sum_{i \in I} \sum_{\substack{j \in J \\ d_{ij} \le D_{\max}}} (RevenuePerOrder - c_{ij}) \cdot x_{ij} - \sum_{j \in J} FixCost_j \cdot y_j$$
        """
    )
    
    st.subheader("5. Constraints")
    st.markdown(
        r"""
        1. **Demand Satisfaction**:
           $$\sum_{\substack{j \in J \\ d_{ij} \le D_{\max}}} x_{ij} \le Demand_i \quad \forall i \in I$$
        
        2. **Store Capacity and Activation**:
           $$\sum_{\substack{i \in I \\ d_{ij} \le D_{\max}}} x_{ij} \le Capacity_j \cdot y_j \quad \forall j \in J$$
           *(If store $j$ is closed ($y_j = 0$), it can serve 0 orders. If open ($y_j = 1$), it cannot exceed its daily capacity).*

        3. **Maximum Service Distance Constraint (The Assignment Enhancement)**:
           $$x_{ij} = 0 \quad \forall (i, j) \text{ where } d_{ij} > D_{\max}$$
           *In high-performance implementation, decision variables $x_{ij}$ are not even instantiated for pairs exceeding $D_{\max}$, pruning over 95% of variables before feeding to solver!*

        4. **Maximum Number of Stores Allowed**:
           $$\sum_{j \in J} y_j \le K$$
        """
    )

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    "Assignment 1: Dark Store Location Optimization Problem | Built with Streamlit, Google OR-Tools, Folium, and Plotly | Ready for Streamlit Cloud Deployment"
)
