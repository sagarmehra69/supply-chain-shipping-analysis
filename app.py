import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="🍬 Nassau Candy Dashboard", layout="wide")

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .kpi-box {
    background: #1e1e2e;
    border-radius: 12px;
    padding: 18px 22px;
    text-align: center;
    border-left: 5px solid #7c3aed;
    height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .kpi-label { color: #a0aec0; font-size: 13px; font-weight: 600; letter-spacing: .05em; }
  .kpi-value { color: #ffffff; font-size: 32px; font-weight: 800; margin: 6px 0; }
  .kpi-delta { font-size: 12px; }
  section[data-testid="stSidebar"] { background-color: #12121f; }
</style>
""", unsafe_allow_html=True)

st.title("🚚 Nassau Candy Distributor")
st.markdown("**Factory-to-Customer Shipping Route Efficiency Dashboard**")

# ── Factory data ───────────────────────────────────────────────────────────────
FACTORIES = {
    "Lot's O' Nuts":      {"lat": 32.881893, "lon": -111.768036},
    "Wicked Choccy's":    {"lat": 32.076176, "lon": -81.088371},
    "Sugar Shack":        {"lat": 48.11914,  "lon": -96.18115},
    "Secret Factory":     {"lat": 41.446333, "lon": -90.565487},
    "The Other Factory":  {"lat": 35.1175,   "lon": -89.971107},
}

PRODUCT_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise":   "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows":           "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious":      "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate":          "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel":   "Wicked Choccy's",
    "Laffy Taffy":                         "Sugar Shack",
    "SweeTARTS":                           "Sugar Shack",
    "Nerds":                               "Sugar Shack",
    "Fun Dip":                             "Sugar Shack",
    "Fizzy Lifting Drinks":                "Sugar Shack",
    "Everlasting Gobstopper":              "Secret Factory",
    "Lickable Wallpaper":                  "Secret Factory",
    "Wonka Gum":                           "Secret Factory",
    "Hair Toffee":                         "The Other Factory",
    "Kazookles":                           "The Other Factory",
}

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("Nassau Candy Distributor.csv")
        df["Order Date"] = pd.to_datetime(df["Order Date"], format='%d-%m-%Y', errors='coerce')
        df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  format='%d-%m-%Y', errors='coerce')
        df = df.dropna(subset=['Order Date'])
        df["Lead Time"]  = (df["Ship Date"] - df["Order Date"]).dt.days
        df = df[df["Lead Time"] >= 0].copy()
        df["Factory"]    = df["Product Name"].map(PRODUCT_FACTORY)
        df["Route"]      = df["Factory"] + " → " + df["Country/Region"] + " - " + df["State/Province"]
        df["Month"]      = df["Order Date"].dt.to_period("M").astype(str)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()
st.success(f"✅ Loaded {len(df):,} shipments across {df['State/Province'].nunique()} states")

# ── Sidebar filters ────────────────────────────────────────────────────────────
st.sidebar.header("🔧 Filters")

min_d, max_d = df["Order Date"].min().date(), df["Order Date"].max().date()
date_start = st.sidebar.date_input("Start Date", min_d, min_value=min_d, max_value=max_d)
date_end   = st.sidebar.date_input("End Date",   max_d, min_value=min_d, max_value=max_d)

ship_modes = st.sidebar.multiselect(
    "Ship Mode", df["Ship Mode"].unique(), default=list(df["Ship Mode"].unique())
)

regions = st.sidebar.multiselect(
    "Region", df["Region"].unique(), default=list(df["Region"].unique())
)

divisions = st.sidebar.multiselect(
    "Division", df["Division"].unique(), default=list(df["Division"].unique())
)

all_states = sorted(df["State/Province"].unique())
selected_states = st.sidebar.multiselect("State/Province (optional)", all_states)

delay_threshold = st.sidebar.slider(
    "Delay Threshold (days)", min_value=1, max_value=30, value=7,
    help="Shipments taking longer than this are considered delayed"
)

show_delayed_only = st.sidebar.checkbox(
    "Show only delayed shipments", value=False,
    help="Filter to show only shipments exceeding the delay threshold"
)

view_mode = st.sidebar.radio(
    "View Mode", ["Summary", "Detailed"], index=0,
    help="Summary: Key metrics and overviews. Detailed: Full analysis with trends and drill-downs."
)

# ── Apply filters ──────────────────────────────────────────────────────────────
fdf = df[
    (df["Order Date"].dt.date >= date_start) &
    (df["Order Date"].dt.date <= date_end) &
    (df["Ship Mode"].isin(ship_modes)) &
    (df["Region"].isin(regions)) &
    (df["Division"].isin(divisions))
].copy()

if selected_states:
    fdf = fdf[fdf["State/Province"].isin(selected_states)]

if show_delayed_only:
    fdf = fdf[fdf["Lead Time"] > delay_threshold]

if fdf.empty:
    st.error("⚠️ No data matches your filters. Please adjust the sidebar.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────────
st.markdown("## 📊 Key Performance Indicators")

avg_lead    = fdf["Lead Time"].mean()
median_lead = fdf["Lead Time"].median()
total       = len(fdf)
delayed     = len(fdf[fdf["Lead Time"] > delay_threshold])
delay_pct   = delayed / total * 100
total_sales = fdf["Sales"].sum()
total_profit= fdf["Gross Profit"].sum()
efficiency_score = 100 - (avg_lead / fdf["Lead Time"].max() * 100) if fdf["Lead Time"].max() > 0 else 100

c1, c2, c3, c4, c5, c6 = st.columns(6)
for col, label, val in zip(
    [c1, c2, c3, c4, c5, c6],
    ["⏱️ Avg Lead Time", "📦 Total Shipments", f"⚠️ Delayed (>{delay_threshold}d)", "💰 Total Sales", "📈 Gross Profit", "🏆 Efficiency Score"],
    [f"{avg_lead:.1f} days", f"{total:,}", f"{delayed:,} ({delay_pct:.1f}%)", f"${total_sales:,.0f}", f"${total_profit:,.0f}", f"{efficiency_score:.1f}%"]
):
    col.markdown(f"""
    <div class="kpi-box">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{val}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Interactive Features ────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1])
with col_left:
    if st.button("🔄 Reset All Filters", help="Reset to default filters"):
        st.rerun()
with col_right:
    csv_data = fdf.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data",
        data=csv_data,
        file_name="filtered_shipments.csv",
        mime="text/csv",
        help="Download the current filtered dataset as CSV"
    )

st.markdown("---")

# ── Tab layout ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏆 Route Efficiency", "🗺️ Geographic Map", "🚚 Ship Mode Analysis", "🔍 Route Drill-Down", "🚧 Bottlenecks", "📋 Executive Summary"
])

# ─── TAB 1: Route Efficiency ───────────────────────────────────────────────────
with tab1:
    st.markdown("### Route Performance Leaderboard")

    route_stats = (
        fdf.groupby("Route")
        .agg(
            Avg_Lead_Time=("Lead Time", "mean"),
            Shipments=("Lead Time", "count"),
            Delayed=(  "Lead Time", lambda x: (x > delay_threshold).sum()),
            Std_Dev=("Lead Time", "std"),
        )
        .round(2)
        .reset_index()
    )
    route_stats["Delay %"]          = (route_stats["Delayed"] / route_stats["Shipments"] * 100).round(1)
    route_stats["Efficiency Score"] = (
        100 - (route_stats["Avg_Lead_Time"] / route_stats["Avg_Lead_Time"].max() * 100)
    ).round(1)
    route_stats.columns = ["Route", "Avg Lead Time (d)", "Shipments", "Delayed", "Std Dev", "Delay %", "Efficiency Score"]

    col_f, col_s = st.columns(2)
    with col_f:
        st.subheader("🥇 Top 10 Fastest Routes")
        st.dataframe(
            route_stats.sort_values("Avg Lead Time (d)").head(10)
                       .reset_index(drop=True),
            width='stretch'
        )
    with col_s:
        st.subheader("🐢 Bottom 10 Slowest Routes")
        st.dataframe(
            route_stats.sort_values("Avg Lead Time (d)", ascending=False).head(10)
                       .reset_index(drop=True),
            width='stretch'
        )

    st.markdown("### Lead Time Distribution by Factory")
    fig_box = px.box(
        fdf, x="Factory", y="Lead Time", color="Factory",
        title="Lead Time Distribution per Factory",
        labels={"Lead Time": "Lead Time (days)"},
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    fig_box.update_layout(showlegend=False)
    st.plotly_chart(fig_box, width='stretch')

    if view_mode == "Detailed":
        st.markdown("### Monthly Average Lead Time Trend")
        monthly = fdf.groupby("Month")["Lead Time"].mean().reset_index()
        fig_trend = px.line(monthly, x="Month", y="Lead Time", markers=True,
                            title="Avg Lead Time Over Time",
                            labels={"Lead Time": "Avg Lead Time (days)"})
        fig_trend.add_hline(y=delay_threshold, line_dash="dash", line_color="red",
                            annotation_text=f"Threshold ({delay_threshold}d)")
        st.plotly_chart(fig_trend, width='stretch')

# ─── TAB 2: Geographic Map ─────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🗺️ US Shipping Efficiency Heatmap")

    # State-level aggregation — need abbreviation codes
    STATE_ABBREV = {
        "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
        "Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA",
        "Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
        "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
        "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
        "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH",
        "New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC",
        "North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA",
        "Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN",
        "Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA",
        "West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY","District of Columbia":"DC",
    }

    state_stats = (
        fdf.groupby("State/Province")
        .agg(
            avg_lead=("Lead Time", "mean"),
            shipments=("Lead Time", "count"),
            delayed=("Lead Time", lambda x: (x > delay_threshold).sum())
        )
        .reset_index()
    )
    state_stats["delay_pct"] = (state_stats["delayed"] / state_stats["shipments"] * 100).round(1)
    state_stats["code"]      = state_stats["State/Province"].map(STATE_ABBREV)

    metric_choice = st.radio(
        "Color map by:", ["Avg Lead Time", "Shipment Volume", "Delay %"],
        horizontal=True
    )
    metric_map = {"Avg Lead Time": "avg_lead", "Shipment Volume": "shipments", "Delay %": "delay_pct"}
    metric_col = metric_map[metric_choice]
    color_label= {"avg_lead": "Avg Lead Time (d)", "shipments": "Shipments", "delay_pct": "Delay %"}[metric_col]

    fig_map = px.choropleth(
        state_stats.dropna(subset=["code"]),
        locations="code",
        locationmode="USA-states",
        color=metric_col,
        scope="usa",
        hover_name="State/Province",
        hover_data={"avg_lead": ":.1f", "shipments": True, "delay_pct": ":.1f%", "code": False},
        color_continuous_scale="Plasma",
        labels={metric_col: color_label},
        title=f"US States — {metric_choice}"
    )

    # Overlay factory pins
    factory_df = pd.DataFrame([
        {"name": k, "lat": v["lat"], "lon": v["lon"]} for k, v in FACTORIES.items()
    ])
    fig_map.add_trace(go.Scattergeo(
        lat=factory_df["lat"],
        lon=factory_df["lon"],
        text=factory_df["name"],
        mode="markers+text",
        textposition="top center",
        marker=dict(size=14, color="#7c3aed", symbol="star"),
        name="Factories"
    ))
    fig_map.update_layout(height=550, geo=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_map, width='stretch')

    st.markdown("### Regional Summary")
    reg_stats = (
        fdf.groupby("Region")
        .agg(
            Avg_Lead_Time=("Lead Time", "mean"),
            Total_Shipments=("Lead Time", "count"),
            Delay_Rate=("Lead Time", lambda x: f"{(x > delay_threshold).mean()*100:.1f}%")
        )
        .round(2).reset_index()
    )
    st.dataframe(reg_stats, width='stretch')

# ─── TAB 3: Ship Mode Analysis ─────────────────────────────────────────────────
with tab3:
    st.markdown("### Ship Mode Performance Comparison")

    fig_box2 = px.box(
        fdf, x="Ship Mode", y="Lead Time", color="Ship Mode",
        title="Lead Time Distribution by Ship Mode",
        labels={"Lead Time": "Lead Time (days)"},
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    fig_box2.add_hline(y=delay_threshold, line_dash="dash", line_color="red",
                       annotation_text=f"Delay threshold ({delay_threshold}d)")
    fig_box2.update_layout(showlegend=False)
    st.plotly_chart(fig_box2, width='stretch')

    mode_stats = (
        fdf.groupby("Ship Mode")
        .agg(
            Avg_Lead_Time=("Lead Time", "mean"),
            Median_Lead_Time=("Lead Time", "median"),
            Shipments=("Lead Time", "count"),
            Delay_Count=("Lead Time", lambda x: (x > delay_threshold).sum()),
            Avg_Sales=("Sales", "mean"),
            Avg_Cost=("Cost", "mean"),
        )
        .round(2).reset_index()
    )
    mode_stats["Delay %"] = (mode_stats["Delay_Count"] / mode_stats["Shipments"] * 100).round(1)
    st.dataframe(mode_stats, width='stretch')
    st.markdown("**Cost-Time Tradeoffs**: Faster ship modes (e.g., First Class) have lower lead times but higher costs. Standard Class balances cost and time effectively.")

    col_a, col_b = st.columns(2)
    with col_a:
        fig_vol = px.bar(
            mode_stats, x="Ship Mode", y="Shipments", color="Ship Mode",
            title="Shipment Volume by Ship Mode",
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_vol.update_layout(showlegend=False)
        st.plotly_chart(fig_vol, width='stretch')
    with col_b:
        fig_dp = px.bar(
            mode_stats, x="Ship Mode", y="Delay %", color="Ship Mode",
            title="Delay Rate by Ship Mode (%)",
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_dp.update_layout(showlegend=False)
        st.plotly_chart(fig_dp, width='stretch')

    st.markdown("### Ship Mode × Division Performance")
    heatmap_data = (
        fdf.groupby(["Division", "Ship Mode"])["Lead Time"]
        .mean().round(1).reset_index()
        .pivot(index="Division", columns="Ship Mode", values="Lead Time")
    )
    fig_heat = px.imshow(
        heatmap_data, text_auto=True, color_continuous_scale="Plasma",
        title="Avg Lead Time Heatmap (Division × Ship Mode)"
    )
    st.plotly_chart(fig_heat, width='stretch')

# ─── TAB 4: Route Drill-Down ───────────────────────────────────────────────────
with tab4:
    st.markdown("### 🔍 State-Level Performance Insights")

    drill_state = st.selectbox("Select a State", sorted(fdf["State/Province"].unique()))
    state_df = fdf[fdf["State/Province"] == drill_state]

    d1, d2, d3 = st.columns(3)
    d1.metric("Total Shipments", len(state_df))
    d2.metric("Avg Lead Time",   f"{state_df['Lead Time'].mean():.1f} days")
    d3.metric("Delay Rate",      f"{(state_df['Lead Time'] > delay_threshold).mean()*100:.1f}%")

    col_l, col_r = st.columns(2)
    with col_l:
        fig_prod = px.bar(
            state_df.groupby("Product Name")["Lead Time"].mean().reset_index().sort_values("Lead Time"),
            x="Lead Time", y="Product Name", orientation="h", color="Lead Time",
            color_continuous_scale="Plasma",
            title=f"Avg Lead Time by Product — {drill_state}"
        )
        st.plotly_chart(fig_prod, width='stretch')
    with col_r:
        fig_mode2 = px.pie(
            state_df, names="Ship Mode", title=f"Ship Mode Mix — {drill_state}",
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        st.plotly_chart(fig_mode2, width='stretch')

    st.markdown("#### Order-Level Shipment Timeline (last 200 orders)")
    timeline_df = state_df.sort_values("Order Date", ascending=False).head(200)[
        ["Order ID", "Order Date", "Ship Date", "Lead Time", "Ship Mode", "Product Name", "Factory", "Sales"]
    ].copy()
    timeline_df["Order Date"] = timeline_df["Order Date"].dt.strftime("%Y-%m-%d")
    timeline_df["Ship Date"]  = timeline_df["Ship Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(timeline_df.reset_index(drop=True), width='stretch')

    st.markdown("### 🏭 Factory Performance Overview")
    factory_stats = (
        fdf.groupby("Factory")
        .agg(
            Avg_Lead_Time=("Lead Time", "mean"),
            Total_Shipments=("Lead Time", "count"),
            Delay_Rate=("Lead Time", lambda x: (x > delay_threshold).mean() * 100),
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Gross Profit", "sum"),
        )
        .round(2).reset_index()
    )
    st.dataframe(factory_stats, width='stretch')

    fig_fac = px.scatter(
        factory_stats, x="Avg_Lead_Time", y="Delay_Rate", size="Total_Shipments",
        color="Factory", text="Factory",
        title="Factory Efficiency Quadrant (Avg Lead Time vs Delay Rate)",
        labels={"Avg_Lead_Time": "Avg Lead Time (d)", "Delay_Rate": "Delay Rate (%)"},
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    fig_fac.update_traces(textposition="top center")
    st.plotly_chart(fig_fac, width='stretch')

# --- TAB 5: Bottlenecks -------------------------------------------------
with tab5:
    st.markdown("### 🚧 High-Volume Bottleneck States")
    
    # Shipment volume
    volume = fdf.groupby('State/Province').size()
    
    # Avg lead time
    performance = fdf.groupby('State/Province')['Lead Time'].mean()
    
    # Combine both
    bottleneck_df = pd.DataFrame({
        'Volume': volume,
        'Avg_Lead_Time': performance
    })
    
    # Sort for bottleneck detection (high volume, high lead time)
    bottleneck_df = bottleneck_df.sort_values(by=['Volume', 'Avg_Lead_Time'], ascending=False).head(10)
    
    st.dataframe(bottleneck_df.reset_index(), width='stretch')
    
    st.markdown("States with high shipment volumes and poor performance (long lead times) are potential bottlenecks.")

# --- TAB 6: Executive Summary -------------------------------------------------
with tab6:
    st.markdown("### 📋 Executive Summary")
    
    # Data Overview
    st.markdown("#### 📊 Data Overview")
    st.markdown(f"""
    - **Total Shipments Analyzed**: {total:,}
    - **Date Range**: {date_start} to {date_end}
    - **States Covered**: {fdf['State/Province'].nunique()}
    - **Regions**: {', '.join(sorted(fdf['Region'].unique()))}
    - **Divisions**: {', '.join(sorted(fdf['Division'].unique()))}
    - **Ship Modes**: {', '.join(sorted(fdf['Ship Mode'].unique()))}
    """)
    
    # Key Performance Indicators
    st.markdown("#### 🏆 Key Performance Indicators")
    st.markdown(f"""
    - **Average Lead Time**: {avg_lead:.1f} days (Median: {median_lead:.1f} days)
    - **Efficiency Score**: {efficiency_score:.1f}% (Higher is better)
    - **Delay Rate**: {delay_pct:.1f}% (Shipments >{delay_threshold} days)
    - **Total Sales**: ${total_sales:,.0f}
    - **Total Gross Profit**: ${total_profit:,.0f}
    - **Profit Margin**: {(total_profit / total_sales * 100):.1f}% if total_sales > 0 else 'N/A'
    """)
    
    # Route Insights
    route_insights = (
        fdf.groupby("Route")
        .agg(
            Avg_Lead_Time=("Lead Time", "mean"),
            Shipments=("Lead Time", "count"),
            Delay_Rate=("Lead Time", lambda x: (x > delay_threshold).mean() * 100)
        )
        .round(2)
        .sort_values("Avg_Lead_Time")
    )
    top_route = route_insights.head(1).index[0] if not route_insights.empty else "N/A"
    worst_route = route_insights.tail(1).index[0] if not route_insights.empty else "N/A"
    
    st.markdown("#### 🏭 Route Performance Insights")
    st.markdown(f"""
    - **Top Performing Route**: {top_route} (Avg Lead Time: {route_insights.loc[top_route, 'Avg_Lead_Time']:.1f} days)
    - **Worst Performing Route**: {worst_route} (Avg Lead Time: {route_insights.loc[worst_route, 'Avg_Lead_Time']:.1f} days)
    - **Routes with High Volume (>100 shipments)**: {len(route_insights[route_insights['Shipments'] > 100])}
    - **Routes with Low Delay Rate (<10%)**: {len(route_insights[route_insights['Delay_Rate'] < 10])}
    """)
    
    # Ship Mode Insights
    mode_insights = (
        fdf.groupby("Ship Mode")
        .agg(
            Avg_Lead_Time=("Lead Time", "mean"),
            Shipments=("Lead Time", "count"),
            Avg_Cost=("Cost", "mean"),
            Avg_Sales=("Sales", "mean")
        )
        .round(2)
    )
    fastest_mode = mode_insights['Avg_Lead_Time'].idxmin()
    slowest_mode = mode_insights['Avg_Lead_Time'].idxmax()
    cost_time_ratio = mode_insights['Avg_Lead_Time'] / mode_insights['Avg_Cost']
    best_balance_mode = cost_time_ratio.idxmin()
    
    st.markdown("#### 🚚 Ship Mode Analysis")
    st.markdown(f"""
    - **Fastest Ship Mode**: {fastest_mode} (Avg Lead Time: {mode_insights.loc[fastest_mode, 'Avg_Lead_Time']:.1f} days)
    - **Slowest Ship Mode**: {slowest_mode} (Avg Lead Time: {mode_insights.loc[slowest_mode, 'Avg_Lead_Time']:.1f} days)
    - **Most Used Mode**: {mode_insights['Shipments'].idxmax()} ({mode_insights['Shipments'].max():,} shipments)
    - **Best Cost-Time Balance**: {best_balance_mode} (Ratio: {cost_time_ratio.loc[best_balance_mode]:.3f}, Lead Time: {mode_insights.loc[best_balance_mode, 'Avg_Lead_Time']:.1f}d, Avg Cost: ${mode_insights.loc[best_balance_mode, 'Avg_Cost']:.2f})
    """)
    
    # Geographic Insights
    state_insights = (
        fdf.groupby("State/Province")
        .agg(
            Avg_Lead_Time=("Lead Time", "mean"),
            Shipments=("Lead Time", "count"),
            Delay_Rate=("Lead Time", lambda x: (x > delay_threshold).mean() * 100)
        )
        .round(2)
    )
    best_state = state_insights['Avg_Lead_Time'].idxmin()
    worst_state = state_insights['Avg_Lead_Time'].idxmax()
    
    st.markdown("#### 🗺️ Geographic Performance")
    st.markdown(f"""
    - **Best Performing State**: {best_state} (Avg Lead Time: {state_insights.loc[best_state, 'Avg_Lead_Time']:.1f} days)
    - **Worst Performing State**: {worst_state} (Avg Lead Time: {state_insights.loc[worst_state, 'Avg_Lead_Time']:.1f} days)
    - **High-Volume Bottleneck States**: {', '.join(bottleneck_df.head(3).index.tolist()) if not bottleneck_df.empty else 'None identified'}
    - **States with >20% Delay Rate**: {len(state_insights[state_insights['Delay_Rate'] > 20])}
    """)
    
    # Division Insights
    division_insights = (
        fdf.groupby("Division")
        .agg(
            Avg_Lead_Time=("Lead Time", "mean"),
            Shipments=("Lead Time", "count"),
            Total_Sales=("Sales", "sum"),
            Delay_Rate=("Lead Time", lambda x: (x > delay_threshold).mean() * 100)
        )
        .round(2)
    )
    top_division = division_insights['Total_Sales'].idxmax()
    
    st.markdown("#### 📂 Division Analysis")
    st.markdown(f"""
    - **Top Revenue Division**: {top_division} (${division_insights.loc[top_division, 'Total_Sales']:,.0f})
    - **Divisions Count**: {len(division_insights)}
    - **Division with Lowest Delay Rate**: {division_insights['Delay_Rate'].idxmin()} ({division_insights['Delay_Rate'].min():.1f}%)
    """)
    
    # Trends (if detailed view)
    if view_mode == "Detailed":
        monthly_trend = fdf.groupby("Month")["Lead Time"].mean().round(2)
        improving = monthly_trend.iloc[-1] < monthly_trend.iloc[0] if len(monthly_trend) > 1 else False
        st.markdown("#### 📈 Trends")
        st.markdown(f"""
        - **Lead Time Trend**: {'Improving' if improving else 'Worsening'} over time
        - **Recent Avg Lead Time**: {monthly_trend.iloc[-1]:.1f} days (Latest month)
        - **Peak Month**: {monthly_trend.idxmax()} ({monthly_trend.max():.1f} days)
        """)
    
    # Recommendations
    st.markdown("#### 💡 Recommendations")
    recommendations = []
    if avg_lead > delay_threshold:
        recommendations.append(f"Reduce average lead time below {delay_threshold} days through route optimization")
    if delay_pct > 15:
        recommendations.append("Investigate and resolve causes of high delay rates (>15%)")
    if len(bottleneck_df) > 0:
        recommendations.append(f"Focus on bottleneck states: {', '.join(bottleneck_df.head(2).index.tolist())}")
    recommendations.append("Leverage Standard Class for cost-effective shipping")
    recommendations.append("Monitor division-specific performance for targeted improvements")
    if view_mode == "Detailed" and not improving:
        recommendations.append("Address worsening lead time trends through process improvements")
    
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"{i}. {rec}")
    
    st.markdown("---")
    st.markdown("**This dashboard provides data-driven insights for Nassau Candy Distributor's logistics optimization, enabling informed decisions to improve efficiency and customer satisfaction.**")

