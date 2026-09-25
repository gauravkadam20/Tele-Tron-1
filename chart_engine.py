"""Dynamic Visualization & GPS Fleet Mapping Engine for Tele-Tron-1.

Intelligently detects the optimal visualization type (GPS Fleet Map, Time Series Line,
Categorical Bar, Multi-variable Scatter, or KPI Metric Cards) and renders interactive
Plotly or Streamlit visualizations.
"""

from typing import Optional, Dict, Any, Tuple, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Standard color palette aligned with Tele-Tron-1 theme
COLOR_PALETTE = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4", "#EC4899"]


def has_gps_coordinates(df: pd.DataFrame) -> Tuple[bool, Optional[str], Optional[str]]:
    """Checks if DataFrame contains valid GPS latitude and longitude columns."""
    lat_col = None
    lon_col = None

    lat_candidates = ["vehicle_gps_latitude", "latitude", "lat"]
    lon_candidates = ["vehicle_gps_longitude", "longitude", "lon", "lng"]

    for col in df.columns:
        col_lower = col.lower()
        if not lat_col and any(c == col_lower for c in lat_candidates):
            lat_col = col
        if not lon_col and any(c == col_lower for c in lon_candidates):
            lon_col = col

    if lat_col and lon_col:
        # Check that they have numeric data
        if pd.api.types.is_numeric_dtype(df[lat_col]) and pd.api.types.is_numeric_dtype(df[lon_col]):
            return True, lat_col, lon_col

    return False, None, None


def detect_best_chart_type(df: pd.DataFrame) -> str:
    """Automatically determines the best chart type for a query result.
    
    Returns:
        One of: 'map', 'line', 'bar', 'scatter', 'kpi', 'none'
    """
    if df is None or len(df) == 0:
        return "none"

    # 1. GPS Fleet Map
    has_gps, _, _ = has_gps_coordinates(df)
    if has_gps:
        return "map"

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    text_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    
    # Check for date / time column
    time_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]

    # 2. KPI Metric Cards (Single aggregate row with 1 to 4 numeric values)
    if len(df) == 1 and len(numeric_cols) > 0 and len(text_cols) == 0:
        return "kpi"

    # 3. Time Series Line Chart
    if time_cols and len(numeric_cols) >= 1:
        return "line"

    # 4. Categorical Bar Chart (Grouped aggregate with 1 category and 1+ metrics)
    if len(text_cols) >= 1 and len(numeric_cols) >= 1:
        return "bar"

    # 5. Scatter Plot (Correlation between two numeric columns without category)
    if len(numeric_cols) >= 2 and len(df) > 5:
        return "scatter"

    # 6. Fallback Bar Chart if numeric columns exist
    if len(numeric_cols) >= 1:
        return "bar"

    return "none"


def build_gps_fleet_map(df: pd.DataFrame, lat_col: str, lon_col: str) -> go.Figure:
    """Builds an interactive GPS Fleet Map using Plotly OpenStreetMap tiles."""
    plot_df = df.dropna(subset=[lat_col, lon_col]).copy()
    
    # Choose color and hover data
    color_col = None
    if "risk_classification" in plot_df.columns:
        color_col = "risk_classification"
    elif "delay_probability" in plot_df.columns:
        color_col = "delay_probability"

    hover_cols = [c for c in plot_df.columns if c not in [lat_col, lon_col]][:5]

    fig = px.scatter_map(
        plot_df,
        lat=lat_col,
        lon=lon_col,
        color=color_col,
        hover_data=hover_cols,
        zoom=3,
        height=500,
        color_discrete_sequence=COLOR_PALETTE,
        title="🛰️ Tele-Tron-1 GPS Fleet Telematics Map",
    )
    fig.update_layout(
        map_style="open-street-map",
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def build_line_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """Builds an interactive time series line chart."""
    time_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not time_cols or not numeric_cols:
        return None

    x_col = time_cols[0]
    plot_df = df.copy()
    try:
        plot_df[x_col] = pd.to_datetime(plot_df[x_col])
        plot_df = plot_df.sort_values(x_col)
    except Exception:
        pass

    y_cols = numeric_cols[:4]  # Maximum 4 lines to keep visualization clean

    fig = px.line(
        plot_df,
        x=x_col,
        y=y_cols,
        markers=True,
        color_discrete_sequence=COLOR_PALETTE,
        title=f"📈 Time Trend: {', '.join(y_cols)} over {x_col}",
    )
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def build_bar_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """Builds an interactive categorical bar chart."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    text_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()

    if not numeric_cols:
        return None

    if text_cols:
        x_col = text_cols[0]
    else:
        x_col = df.columns[0]

    y_cols = [c for c in numeric_cols if c != x_col][:3]
    if not y_cols:
        return None

    fig = px.bar(
        df,
        x=x_col,
        y=y_cols,
        barmode="group",
        color_discrete_sequence=COLOR_PALETTE,
        title=f"📊 Comparison: {', '.join(y_cols)} by {x_col}",
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def build_scatter_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """Builds an interactive correlation scatter plot."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(numeric_cols) < 2:
        return None

    x_col = numeric_cols[0]
    y_col = numeric_cols[1]
    
    color_col = None
    text_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    if text_cols:
        color_col = text_cols[0]

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        trendline="ols" if len(df) >= 10 else None,
        color_discrete_sequence=COLOR_PALETTE,
        title=f"🎯 Correlation: {y_col} vs {x_col}",
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def render_dynamic_visualization(df: pd.DataFrame, requested_type: Optional[str] = None) -> Tuple[str, Any]:
    """Selects and renders the best visualization figure for a given dataframe.
    
    Returns:
        Tuple of (chart_type, figure_or_metrics)
    """
    chart_type = requested_type or detect_best_chart_type(df)

    if chart_type == "map":
        has_gps, lat_col, lon_col = has_gps_coordinates(df)
        if has_gps and lat_col and lon_col:
            fig = build_gps_fleet_map(df, lat_col, lon_col)
            return "map", fig

    if chart_type == "line":
        fig = build_line_chart(df)
        if fig:
            return "line", fig

    if chart_type == "scatter":
        fig = build_scatter_chart(df)
        if fig:
            return "scatter", fig

    if chart_type == "kpi":
        # Extract dictionary of KPI name -> value
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        kpis = {col: df[col].iloc[0] for col in numeric_cols[:4]}
        return "kpi", kpis

    # Default to bar chart if applicable
    fig = build_bar_chart(df)
    if fig:
        return "bar", fig

    return "table", None
