"""Semantic Business Catalog & Data Dictionary for Tele-Tron-1 Logistics Intelligence."""

from typing import Dict, Any

LOGISTICS_DATA_DICTIONARY: Dict[str, Dict[str, Any]] = {
    "timestamp": {
        "type": "TEXT",
        "description": "UTC timestamp of the shipment telematics reading (format: YYYY-MM-DD HH:MM:SS).",
        "unit_or_range": "Datetime",
    },
    "vehicle_gps_latitude": {
        "type": "REAL",
        "description": "Current GPS latitude coordinate of the transport vehicle.",
        "unit_or_range": "Degrees (-90.0 to 90.0)",
    },
    "vehicle_gps_longitude": {
        "type": "REAL",
        "description": "Current GPS longitude coordinate of the transport vehicle.",
        "unit_or_range": "Degrees (-180.0 to 180.0)",
    },
    "fuel_consumption_rate": {
        "type": "REAL",
        "description": "Fuel burn rate of the freight vehicle.",
        "unit_or_range": "Liters per 100km (or gal/hr)",
    },
    "eta_variation_hours": {
        "type": "REAL",
        "description": "Deviation from scheduled ETA. Positive values denote arrival delays beyond ETA; negative values denote early arrivals.",
        "unit_or_range": "Hours (e.g., +2.5 = 2.5 hours late)",
    },
    "traffic_congestion_level": {
        "type": "REAL",
        "description": "Real-time traffic congestion score along the corridor.",
        "unit_or_range": "Index scale 1.0 (light) to 10.0 (severe congestion)",
    },
    "warehouse_inventory_level": {
        "type": "REAL",
        "description": "Available stock or capacity units at destination/origin warehouse.",
        "unit_or_range": "Units in stock",
    },
    "loading_unloading_time": {
        "type": "REAL",
        "description": "Duration spent at loading docks during freight handling.",
        "unit_or_range": "Hours",
    },
    "handling_equipment_availability": {
        "type": "REAL",
        "description": "Availability ratio of forklifts, cranes, and automated handling equipment.",
        "unit_or_range": "Ratio 0.0 (none available) to 1.0 (fully available)",
    },
    "order_fulfillment_status": {
        "type": "REAL",
        "description": "Progress score of order packing, verification, and dispatch.",
        "unit_or_range": "Progress ratio 0.0 (unfulfilled) to 1.0 (fully fulfilled)",
    },
    "weather_condition_severity": {
        "type": "REAL",
        "description": "Impact of adverse weather (storms, snow, high winds) on transport.",
        "unit_or_range": "Index scale 0.0 (clear) to 1.0 (extreme weather)",
    },
    "port_congestion_level": {
        "type": "REAL",
        "description": "Vessel wait times and container yard dwell severity at ports.",
        "unit_or_range": "Index scale 1.0 (smooth) to 10.0 (gridlock)",
    },
    "shipping_costs": {
        "type": "REAL",
        "description": "Total freight charge incurred for the shipment.",
        "unit_or_range": "USD ($)",
    },
    "supplier_reliability_score": {
        "type": "REAL",
        "description": "Historical vendor reliability rating based on on-time delivery and SLA compliance.",
        "unit_or_range": "Score 0.0 (unreliable) to 1.0 (flawless reliability)",
    },
    "lead_time_days": {
        "type": "REAL",
        "description": "Total procurement and transit turnaround time from purchase order to delivery.",
        "unit_or_range": "Days",
    },
    "historical_demand": {
        "type": "REAL",
        "description": "Average volume of shipments requested over historical cycle.",
        "unit_or_range": "Volume units",
    },
    "iot_temperature": {
        "type": "REAL",
        "description": "Cold-chain IoT sensor temperature inside the cargo container.",
        "unit_or_range": "Celsius (°C)",
    },
    "cargo_condition_status": {
        "type": "REAL",
        "description": "Health status of cargo monitoring for damage, shock, or spoilage.",
        "unit_or_range": "Health index 0.0 (damaged/spoiled) to 1.0 (pristine)",
    },
    "route_risk_level": {
        "type": "REAL",
        "description": "Composite security and terrain hazard rating for the active transit path.",
        "unit_or_range": "Index scale 1.0 (safe) to 10.0 (extreme hazard)",
    },
    "customs_clearance_time": {
        "type": "REAL",
        "description": "Duration required for regulatory inspections, duties, and customs release.",
        "unit_or_range": "Hours (or days)",
    },
    "driver_behavior_score": {
        "type": "REAL",
        "description": "Safety telematics score measuring harsh braking, speeding, and cornering.",
        "unit_or_range": "Safety score 0.0 (dangerous driving) to 1.0 (exemplary driving)",
    },
    "fatigue_monitoring_score": {
        "type": "REAL",
        "description": "In-cab driver drowsiness and fatigue indicator.",
        "unit_or_range": "Risk index 0.0 (alert) to 1.0 (severe fatigue risk)",
    },
    "disruption_likelihood_score": {
        "type": "REAL",
        "description": "Predictive model probability of supply chain disruption.",
        "unit_or_range": "Probability 0.0 to 1.0",
    },
    "delay_probability": {
        "type": "REAL",
        "description": "Estimated likelihood of shipment arriving past contracted SLA.",
        "unit_or_range": "Probability 0.0 (on-time) to 1.0 (certain delay). Values >= 0.70 represent high delay risk.",
    },
    "risk_classification": {
        "type": "TEXT",
        "description": "Executive risk category assigned to the shipment.",
        "unit_or_range": "Categorical: EXACT string values are 'Low Risk', 'Moderate Risk', or 'High Risk'",
    },
    "delivery_time_deviation": {
        "type": "REAL",
        "description": "Variance between actual delivery time and scheduled delivery target.",
        "unit_or_range": "Hours",
    },
}

DOMAIN_BUSINESS_RULES = """
BUSINESS DOMAIN RULES & SYNONYMS:
- 'High Risk' shipments: Use `risk_classification = 'High Risk'` or `route_risk_level >= 7.0`.
- 'Delayed shipments' or 'High delay': Use `delay_probability >= 0.70` or `eta_variation_hours > 0`.
- 'Unreliable suppliers': Use `supplier_reliability_score < 0.60`.
- 'Driver fatigue alert': Use `fatigue_monitoring_score >= 0.70`.
- 'Cold chain alert / frozen cargo': Check `iot_temperature` (refrigerated typically 2°C to 8°C; frozen <= -18°C).
- 'Categorical strings': In SQLite text comparisons, match exact strings: 'Low Risk', 'Moderate Risk', 'High Risk'.
"""


def get_data_dictionary_prompt() -> str:
    """Formats the data dictionary and business rules into an LLM context block."""
    lines = ["Table: logistics_data", "Column Definitions:"]
    for col, meta in LOGISTICS_DATA_DICTIONARY.items():
        lines.append(f"- {col} ({meta['type']}): {meta['description']} [Unit/Range: {meta['unit_or_range']}]")

    lines.append("\n" + DOMAIN_BUSINESS_RULES.strip())
    return "\n".join(lines)
