import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# ── Database Connection ──────────────────────────────────────
def get_connection():
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        database=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432),
        sslmode=os.environ.get("PGSSLMODE", "require")
    )

def run_query(sql: str, params=None) -> list[dict]:
    """Execute a SQL query and return list of dicts."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or [])
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def format_rows(rows: list[dict]) -> str:
    """Format query results as readable text."""
    if not rows:
        return "No data found."
    headers = list(rows[0].keys())
    lines = [" | ".join(str(h).upper() for h in headers)]
    lines.append("─" * 80)
    for row in rows:
        lines.append(" | ".join(str(v) if v is not None else "N/A" for v in row.values()))
    return "\n".join(lines)


# ── MCP Server ───────────────────────────────────────────────
mcp = FastMCP(
    "CamelX Analytics Intelligence",
    instructions="""
You are CamelX Analytics Intelligence — an AI assistant for the CamelX camel
management platform built by Octaware Technologies. You help managers, trainers,
veterinarians, and owners extract insights from live camel data stored in the
CamelX Azure PostgreSQL database.

════════════════════════════════════════════════════════
STRICT RULES — NEVER BREAK THESE
════════════════════════════════════════════════════════

RULE 1 — ALWAYS USE MCP TOOLS FOR DOMAIN QUESTIONS
For ANY question about:
  - Camels — count, breed, gender, weight, age, status
  - Health metrics — heart rate, SpO2, temperature, stress, fatigue, blood pressure
  - Races — upcoming races, past results, winners, prize pools
  - Training — sessions, distances, speed, calories, performance ratings
  - Alerts — active alerts, critical issues, severity breakdown
  - Anomalies — AI-detected unresolved anomalies
  - IoT Devices — sensors, trackers, battery levels, device types
  - Diet & Nutrition — diet plans, meal schedules, calorie targets
  - Vendors — subscription plans, monthly revenue
  - Users — staff roles, active user counts
  - AI Models — prediction accuracy, model types
  - Performance Trends — improvement percentages, speed trends
  → You MUST call the appropriate MCP tool FIRST.
  → NEVER answer these from your general training knowledge.
  → NEVER guess, estimate, or invent any number or statistic.

RULE 2 — WHAT TO DO IF NO DATA FOUND
If the MCP tool returns no results:
  → Say clearly: "No data found in CamelX database for your query."
  → Suggest a refined question or different parameters.
  → NEVER fall back to general knowledge to fill the gap.

RULE 3 — GENERAL KNOWLEDGE IS ALLOWED ONLY FOR
  → Explaining concepts (e.g. "what is SpO2", "what is a performance index")
  → Explaining how CamelX platform works
  → General camel care or veterinary education questions
  → Anything NOT related to specific CamelX database records

════════════════════════════════════════════════════════
TOOL SELECTION GUIDE
════════════════════════════════════════════════════════

Use get_camel_stats when user asks:
  → "How many camels are there?"
  → "Show camels by breed / gender / status"
  → "Which camel has the highest performance index?"
  → "Find camel named [name]"
  → "Show oldest / heaviest camels"

Use get_health_metrics when user asks:
  → "What is the average heart rate?"
  → "Show SpO2 / oxygen levels"
  → "Any high stress readings?"
  → "What is the body temperature average?"
  → "Show blood pressure stats"
  → "Health summary for last 24 hours"

Use get_race_data when user asks:
  → "Any upcoming races?"
  → "Who won the last race?"
  → "Show race results"
  → "Which camel has won the most races?"
  → "Total prize pool across all races?"

Use get_training_data when user asks:
  → "How many training sessions completed?"
  → "Which camel has the best training rating?"
  → "Show training performance summary"
  → "Total distance covered in training?"

Use get_alerts_and_anomalies when user asks:
  → "Any active alerts?"
  → "Show critical alerts"
  → "How many unresolved anomalies?"
  → "Any recent alerts?"
  → "What is the alert severity breakdown?"

Use get_iot_devices when user asks:
  → "How many IoT devices are there?"
  → "Any devices with low battery?"
  → "Show devices by type"
  → "Total sensors deployed?"

Use get_diet_info when user asks:
  → "How many active diet plans?"
  → "What is the average calorie target?"
  → "Show meal schedules"

Use get_vendor_and_user_info when user asks:
  → "How many vendors are using CamelX?"
  → "Show subscription plans breakdown"
  → "Total monthly revenue?"
  → "How many active users?"
  → "Show users by role — trainers, vets, owners"

Use get_dashboard_overview when user asks:
  → "Give me a summary / overview"
  → "Show me everything"
  → "CamelX dashboard stats"
  → "What is the overall status?"

════════════════════════════════════════════════════════
RESPONSE FORMAT
════════════════════════════════════════════════════════
Always structure your response as:
  1. Direct answer with the key number or finding
  2. Breakdown table or list (if applicable)
  3. Brief insight or observation about the data
  4. Offer to drill deeper: "Want me to analyze any specific
     camel or metric in more detail?"

Always use clean tables or numbered lists for data results.
For alerts: clearly label severity (Critical / High / Medium / Low).
For rankings: always number them (1, 2, 3...).
Support both English and Arabic camel names when searching.
"""
)

# ════════════════════════════════════════════════════════════
# TOOL 1 — CAMEL MANAGEMENT
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_camel_stats(
    stat_type: str = "total",
    camel_name: str = None,
    limit: int = 10
) -> str:
    """
    Get statistics and information about camels in CamelX.
    Use for any question about camels — count, breed, gender,
    performance, health index, fatigue, age, weight, or searching
    a specific camel by name.

    Args:
        stat_type: Type of stat to fetch. Options:
            "total"         — total camel count
            "by_breed"      — count grouped by breed
            "by_gender"     — count grouped by gender
            "by_status"     — count grouped by status
            "top_performers"— top camels by performance index
            "healthiest"    — top camels by health index
            "most_fatigued" — camels with highest fatigue score
            "by_age"        — camels sorted by age
            "by_weight"     — camels sorted by weight
            "search"        — search camel by name (use camel_name)
        camel_name: Name to search for (used when stat_type="search")
        limit: Number of results to return (default 10)
    """
    try:
        if stat_type == "total":
            rows = run_query("SELECT COUNT(*) as total_camels FROM camels")

        elif stat_type == "by_breed":
            rows = run_query(
                "SELECT breed, COUNT(*) as count FROM camels "
                "GROUP BY breed ORDER BY count DESC"
            )

        elif stat_type == "by_gender":
            rows = run_query(
                "SELECT gender, COUNT(*) as count FROM camels GROUP BY gender"
            )

        elif stat_type == "by_status":
            rows = run_query(
                "SELECT status, COUNT(*) as count FROM camels GROUP BY status"
            )

        elif stat_type == "top_performers":
            rows = run_query(
                "SELECT name, breed, gender, performance_index, health_index, fatigue_score "
                "FROM camels WHERE performance_index IS NOT NULL "
                "ORDER BY performance_index DESC LIMIT %s", [limit]
            )

        elif stat_type == "healthiest":
            rows = run_query(
                "SELECT name, breed, health_index, performance_index, fatigue_score "
                "FROM camels WHERE health_index IS NOT NULL "
                "ORDER BY health_index DESC LIMIT %s", [limit]
            )

        elif stat_type == "most_fatigued":
            rows = run_query(
                "SELECT name, breed, fatigue_score, health_index, performance_index "
                "FROM camels WHERE fatigue_score IS NOT NULL "
                "ORDER BY fatigue_score DESC LIMIT %s", [limit]
            )

        elif stat_type == "by_age":
            rows = run_query(
                "SELECT name, breed, age, gender, health_index "
                "FROM camels ORDER BY age DESC LIMIT %s", [limit]
            )

        elif stat_type == "by_weight":
            rows = run_query(
                "SELECT name, breed, weight, height, age "
                "FROM camels WHERE weight IS NOT NULL "
                "ORDER BY weight DESC LIMIT %s", [limit]
            )

        elif stat_type == "search":
            if not camel_name:
                return "Please provide camel_name to search."
            rows = run_query(
                "SELECT name, name_arabic, age, breed, gender, weight, height, "
                "status, performance_index, health_index, fatigue_score "
                "FROM camels WHERE LOWER(name) LIKE LOWER(%s) LIMIT %s",
                [f"%{camel_name}%", limit]
            )
        else:
            return f"Unknown stat_type: {stat_type}"

        return f"Camel Stats — {stat_type.replace('_', ' ').title()}\n{'═' * 80}\n{format_rows(rows)}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 2 — HEALTH METRICS
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_health_metrics(
    metric_type: str = "summary",
    hours: int = 24
) -> str:
    """
    Get health and vitals data for camels from IoT sensors.
    Use for questions about heart rate, SpO2, temperature,
    stress, fatigue, blood pressure, or overall health summary.

    Args:
        metric_type: Type of health data. Options:
            "summary"        — all vitals averaged
            "heart_rate"     — heart rate stats
            "spo2"           — blood oxygen levels
            "temperature"    — body temperature
            "stress"         — stress levels
            "blood_pressure" — systolic and diastolic BP
            "fatigue"        — fatigue levels
        hours: How many hours back to look (default 24)
    """
    try:
        interval = f"{hours} hours"

        if metric_type == "summary":
            rows = run_query(
                f"""SELECT
                    ROUND(AVG(heart_rate)::numeric,1) as avg_heart_rate,
                    ROUND(AVG(spo2)::numeric,1) as avg_spo2,
                    ROUND(AVG(temperature)::numeric,1) as avg_temperature,
                    ROUND(AVG(stress)::numeric,1) as avg_stress,
                    ROUND(AVG(fatigue)::numeric,1) as avg_fatigue,
                    ROUND(AVG(blood_pressure_sbp)::numeric,1) as avg_systolic_bp,
                    COUNT(*) as total_readings
                FROM health_metrics
                WHERE recorded_at > NOW() - INTERVAL '{interval}'"""
            )

        elif metric_type == "heart_rate":
            rows = run_query(
                f"""SELECT
                    ROUND(AVG(heart_rate)::numeric,1) as avg,
                    ROUND(MIN(heart_rate)::numeric,1) as min,
                    ROUND(MAX(heart_rate)::numeric,1) as max,
                    COUNT(*) as readings
                FROM health_metrics
                WHERE heart_rate IS NOT NULL
                AND recorded_at > NOW() - INTERVAL '{interval}'"""
            )

        elif metric_type == "spo2":
            rows = run_query(
                f"""SELECT
                    ROUND(AVG(spo2)::numeric,1) as avg_spo2,
                    ROUND(MIN(spo2)::numeric,1) as min_spo2,
                    ROUND(MAX(spo2)::numeric,1) as max_spo2
                FROM health_metrics
                WHERE spo2 IS NOT NULL
                AND recorded_at > NOW() - INTERVAL '{interval}'"""
            )

        elif metric_type == "temperature":
            rows = run_query(
                f"""SELECT
                    ROUND(AVG(temperature)::numeric,1) as avg_temp,
                    ROUND(MIN(temperature)::numeric,1) as min_temp,
                    ROUND(MAX(temperature)::numeric,1) as max_temp
                FROM health_metrics
                WHERE temperature IS NOT NULL
                AND recorded_at > NOW() - INTERVAL '{interval}'"""
            )

        elif metric_type == "stress":
            rows = run_query(
                f"""SELECT
                    ROUND(AVG(stress)::numeric,2) as avg_stress,
                    ROUND(MAX(stress)::numeric,2) as max_stress,
                    COUNT(CASE WHEN stress > 0.7 THEN 1 END) as high_stress_count
                FROM health_metrics
                WHERE stress IS NOT NULL
                AND recorded_at > NOW() - INTERVAL '{interval}'"""
            )

        elif metric_type == "blood_pressure":
            rows = run_query(
                f"""SELECT
                    ROUND(AVG(blood_pressure_sbp)::numeric,1) as avg_systolic,
                    ROUND(AVG(blood_pressure_dbp)::numeric,1) as avg_diastolic,
                    ROUND(MAX(blood_pressure_sbp)::numeric,1) as max_systolic
                FROM health_metrics
                WHERE blood_pressure_sbp IS NOT NULL
                AND recorded_at > NOW() - INTERVAL '{interval}'"""
            )

        elif metric_type == "fatigue":
            rows = run_query(
                f"""SELECT
                    ROUND(AVG(fatigue)::numeric,2) as avg_fatigue,
                    ROUND(MAX(fatigue)::numeric,2) as max_fatigue,
                    COUNT(CASE WHEN fatigue > 0.7 THEN 1 END) as high_fatigue_count
                FROM health_metrics
                WHERE fatigue IS NOT NULL
                AND recorded_at > NOW() - INTERVAL '{interval}'"""
            )
        else:
            return f"Unknown metric_type: {metric_type}"

        return f"Health Metrics — {metric_type.replace('_',' ').title()} (Last {hours}h)\n{'═'*80}\n{format_rows(rows)}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 3 — RACE ANALYTICS
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_race_data(
    query_type: str = "results",
    limit: int = 20
) -> str:
    """
    Get race information from CamelX database.
    Use for questions about races — upcoming races, past results,
    winners, prize pools, race counts, or race summaries.

    Args:
        query_type: Type of race data. Options:
            "upcoming"  — future scheduled races
            "results"   — recent race results with positions
            "winners"   — camels with most wins
            "summary"   — total races and prize pool stats
        limit: Number of records to return (default 20)
    """
    try:
        if query_type == "upcoming":
            rows = run_query(
                "SELECT name, location, race_date, distance, "
                "category, age_category, max_participants, prize_pool "
                "FROM races WHERE race_date > NOW() "
                "ORDER BY race_date ASC LIMIT %s", [limit]
            )

        elif query_type == "results":
            rows = run_query(
                """SELECT r.name as race_name, r.location, r.race_date,
                    rr.position, c.name as camel_name,
                    rr.finish_time, rr.average_speed, rr.prize_won
                FROM race_results rr
                JOIN camels c ON c.id = rr.camel_id
                JOIN races r ON r.id = rr.race_id
                ORDER BY r.race_date DESC, rr.position ASC
                LIMIT %s""", [limit]
            )

        elif query_type == "winners":
            rows = run_query(
                """SELECT c.name as camel_name,
                    COUNT(*) as total_wins,
                    ROUND(AVG(rr.average_speed)::numeric,1) as avg_winning_speed,
                    SUM(rr.prize_won) as total_prize_won
                FROM race_results rr
                JOIN camels c ON c.id = rr.camel_id
                WHERE rr.position = 1
                GROUP BY c.name
                ORDER BY total_wins DESC
                LIMIT %s""", [limit]
            )

        elif query_type == "summary":
            rows = run_query(
                """SELECT
                    COUNT(*) as total_races,
                    COUNT(CASE WHEN race_date > NOW() THEN 1 END) as upcoming_races,
                    COUNT(CASE WHEN race_date <= NOW() THEN 1 END) as completed_races,
                    SUM(prize_pool) as total_prize_pool,
                    ROUND(AVG(distance)::numeric,1) as avg_distance_km
                FROM races"""
            )
        else:
            return f"Unknown query_type: {query_type}"

        return f"Race Data — {query_type.title()}\n{'═'*80}\n{format_rows(rows)}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 4 — TRAINING ANALYTICS
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_training_data(
    query_type: str = "summary",
    limit: int = 10
) -> str:
    """
    Get training session data and performance logs from CamelX.
    Use for questions about training sessions, distances covered,
    calories burned, speed, or top training performers.

    Args:
        query_type: Type of training data. Options:
            "summary"    — overall training stats
            "top_camels" — camels with best training ratings
            "recent"     — recent training sessions
        limit: Number of records (default 10)
    """
    try:
        if query_type == "summary":
            rows = run_query(
                """SELECT
                    COUNT(*) as total_sessions,
                    ROUND(AVG(actual_distance)::numeric,1) as avg_distance_km,
                    ROUND(AVG(average_speed)::numeric,1) as avg_speed_kmh,
                    ROUND(AVG(max_speed)::numeric,1) as avg_max_speed,
                    SUM(calories_burned) as total_calories_burned,
                    ROUND(AVG(performance_rating)::numeric,1) as avg_performance_rating
                FROM training_logs"""
            )

        elif query_type == "top_camels":
            rows = run_query(
                """SELECT c.name as camel_name,
                    COUNT(tl.id) as total_sessions,
                    ROUND(AVG(tl.average_speed)::numeric,1) as avg_speed,
                    ROUND(SUM(tl.actual_distance)::numeric,1) as total_distance_km,
                    SUM(tl.calories_burned) as total_calories,
                    ROUND(AVG(tl.performance_rating)::numeric,1) as avg_rating
                FROM training_logs tl
                JOIN camels c ON c.id = tl.camel_id
                GROUP BY c.name
                ORDER BY avg_rating DESC
                LIMIT %s""", [limit]
            )

        elif query_type == "recent":
            rows = run_query(
                """SELECT c.name as camel_name,
                    tl.actual_distance, tl.average_speed,
                    tl.calories_burned, tl.performance_rating,
                    tl.recorded_at
                FROM training_logs tl
                JOIN camels c ON c.id = tl.camel_id
                ORDER BY tl.recorded_at DESC
                LIMIT %s""", [limit]
            )
        else:
            return f"Unknown query_type: {query_type}"

        return f"Training Data — {query_type.replace('_',' ').title()}\n{'═'*80}\n{format_rows(rows)}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 5 — ALERTS & ANOMALIES
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_alerts_and_anomalies(
    query_type: str = "active_alerts",
    limit: int = 10
) -> str:
    """
    Get alerts and anomaly detection data from CamelX.
    Use for questions about active alerts, critical issues,
    recent alerts, or unresolved anomalies detected by AI.

    Args:
        query_type: Type of alert data. Options:
            "active_alerts"    — all active alerts by severity
            "critical_alerts"  — only critical severity alerts
            "recent_alerts"    — latest 10 alerts of any status
            "anomalies"        — unresolved AI-detected anomalies
        limit: Number of records (default 10)
    """
    try:
        if query_type == "active_alerts":
            total = run_query("SELECT COUNT(*) as total FROM alerts WHERE status = 'active'")
            by_severity = run_query(
                "SELECT severity, COUNT(*) as count FROM alerts "
                "WHERE status = 'active' GROUP BY severity ORDER BY count DESC"
            )
            return (
                f"Active Alerts Summary\n{'═'*80}\n"
                f"Total Active: {total[0]['total']}\n\n"
                f"By Severity:\n{format_rows(by_severity)}"
            )

        elif query_type == "critical_alerts":
            rows = run_query(
                """SELECT a.title, a.message, a.alert_type, a.created_at,
                    c.name as camel_name
                FROM alerts a
                LEFT JOIN camels c ON c.id = a.camel_id
                WHERE a.severity = 'critical'
                AND a.status = 'active'
                ORDER BY a.created_at DESC
                LIMIT %s""", [limit]
            )

        elif query_type == "recent_alerts":
            rows = run_query(
                """SELECT a.title, a.severity, a.alert_type,
                    a.status, a.created_at, c.name as camel_name
                FROM alerts a
                LEFT JOIN camels c ON c.id = a.camel_id
                ORDER BY a.created_at DESC
                LIMIT %s""", [limit]
            )

        elif query_type == "anomalies":
            total = run_query(
                "SELECT COUNT(*) as total FROM anomaly_detections WHERE resolved = false"
            )
            by_severity = run_query(
                "SELECT severity, metric_name, COUNT(*) as count "
                "FROM anomaly_detections WHERE resolved = false "
                "GROUP BY severity, metric_name ORDER BY count DESC LIMIT %s", [limit]
            )
            return (
                f"Unresolved Anomalies\n{'═'*80}\n"
                f"Total Unresolved: {total[0]['total']}\n\n"
                f"By Severity & Metric:\n{format_rows(by_severity)}"
            )
        else:
            return f"Unknown query_type: {query_type}"

        return f"Alerts — {query_type.replace('_',' ').title()}\n{'═'*80}\n{format_rows(rows)}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 6 — IoT DEVICES
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_iot_devices(
    query_type: str = "summary"
) -> str:
    """
    Get IoT device information from CamelX.
    Use for questions about devices, sensors, trackers,
    battery levels, or device counts.

    Args:
        query_type: Type of device data. Options:
            "summary"      — total devices, types, battery avg
            "low_battery"  — devices with battery below 20%
            "by_type"      — device count by type
    """
    try:
        if query_type == "summary":
            total = run_query("SELECT COUNT(*) as total_devices FROM iot_devices")
            by_type = run_query(
                "SELECT device_type, COUNT(*) as count FROM iot_devices GROUP BY device_type"
            )
            battery = run_query(
                """SELECT
                    ROUND(AVG(battery_level)::numeric,1) as avg_battery,
                    COUNT(CASE WHEN battery_level < 20 THEN 1 END) as low_battery_devices,
                    COUNT(CASE WHEN battery_level >= 80 THEN 1 END) as healthy_battery_devices
                FROM iot_devices WHERE battery_level IS NOT NULL"""
            )
            return (
                f"IoT Devices Summary\n{'═'*80}\n"
                f"Total Devices: {total[0]['total_devices']}\n\n"
                f"By Type:\n{format_rows(by_type)}\n\n"
                f"Battery Status:\n{format_rows(battery)}"
            )

        elif query_type == "low_battery":
            rows = run_query(
                """SELECT d.device_id, d.device_type, d.battery_level,
                    c.name as camel_name, d.last_sync_at
                FROM iot_devices d
                LEFT JOIN camels c ON c.id = d.camel_id
                WHERE d.battery_level < 20
                ORDER BY d.battery_level ASC"""
            )

        elif query_type == "by_type":
            rows = run_query(
                "SELECT device_type, COUNT(*) as count, "
                "ROUND(AVG(battery_level)::numeric,1) as avg_battery "
                "FROM iot_devices GROUP BY device_type"
            )
        else:
            return f"Unknown query_type: {query_type}"

        return f"IoT Devices — {query_type.replace('_',' ').title()}\n{'═'*80}\n{format_rows(rows)}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 7 — DIET & NUTRITION
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_diet_info(
    query_type: str = "summary"
) -> str:
    """
    Get diet and nutrition data for camels in CamelX.
    Use for questions about diet plans, meals, calorie targets,
    nutrition schedules, or feeding information.

    Args:
        query_type: Type of diet data. Options:
            "summary"  — active plans count and calorie stats
            "meals"    — recent meal details
    """
    try:
        if query_type == "summary":
            rows = run_query(
                """SELECT
                    COUNT(*) as active_diet_plans,
                    ROUND(AVG(total_calories)::numeric,0) as avg_daily_calories,
                    SUM(total_calories) as total_calories_all_plans
                FROM diet_plans WHERE is_active = true"""
            )

        elif query_type == "meals":
            rows = run_query(
                """SELECT m.meal_type, m.scheduled_time,
                    m.calories, m.protein, m.carbs, m.fats, m.water
                FROM meals m
                JOIN diet_plans dp ON dp.id = m.diet_plan_id
                WHERE dp.is_active = true
                LIMIT 20"""
            )
        else:
            return f"Unknown query_type: {query_type}"

        return f"Diet & Nutrition — {query_type.title()}\n{'═'*80}\n{format_rows(rows)}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 8 — VENDORS & USERS
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_vendor_and_user_info(
    query_type: str = "vendors"
) -> str:
    """
    Get vendor subscription and user management data from CamelX.
    Use for questions about vendors, subscriptions, revenue,
    active users, staff roles, trainers, vets, or owners.

    Args:
        query_type: Type of data. Options:
            "vendors"       — vendors by subscription plan and revenue
            "users_by_role" — active users grouped by role
            "user_total"    — total active user count
    """
    try:
        if query_type == "vendors":
            rows = run_query(
                """SELECT subscription_plan,
                    COUNT(*) as vendor_count,
                    SUM(monthly_revenue) as total_monthly_revenue,
                    SUM(camel_count) as total_camels,
                    SUM(device_count) as total_devices
                FROM vendors
                GROUP BY subscription_plan
                ORDER BY total_monthly_revenue DESC"""
            )

        elif query_type == "users_by_role":
            rows = run_query(
                "SELECT role, COUNT(*) as count FROM users "
                "WHERE is_active = true GROUP BY role ORDER BY count DESC"
            )

        elif query_type == "user_total":
            rows = run_query(
                "SELECT COUNT(*) as total_active_users FROM users WHERE is_active = true"
            )
        else:
            return f"Unknown query_type: {query_type}"

        return f"Vendor & User Info — {query_type.replace('_',' ').title()}\n{'═'*80}\n{format_rows(rows)}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 9 — DASHBOARD OVERVIEW
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_dashboard_overview() -> str:
    """
    Get a complete overview of all CamelX data in one shot.
    Use when user asks for a summary, overview, dashboard,
    or 'tell me everything' about CamelX.
    """
    try:
        camels      = run_query("SELECT COUNT(*) as total FROM camels")[0]
        devices     = run_query("SELECT COUNT(*) as total FROM iot_devices")[0]
        alerts      = run_query("SELECT COUNT(*) as total FROM alerts WHERE status = 'active'")[0]
        upcoming    = run_query("SELECT COUNT(*) as total FROM races WHERE race_date > NOW()")[0]
        users       = run_query("SELECT COUNT(*) as total FROM users WHERE is_active = true")[0]
        anomalies   = run_query("SELECT COUNT(*) as total FROM anomaly_detections WHERE resolved = false")[0]
        diet_plans  = run_query("SELECT COUNT(*) as total FROM diet_plans WHERE is_active = true")[0]
        training    = run_query("SELECT COUNT(*) as total FROM training_logs")[0]
        vendors     = run_query("SELECT COUNT(*) as total FROM vendors")[0]

        return f"""
CamelX Dashboard Overview
{'═' * 80}
🐪  Total Camels          : {camels['total']}
📡  IoT Devices           : {devices['total']}
🚨  Active Alerts         : {alerts['total']}
🏁  Upcoming Races        : {upcoming['total']}
👥  Active Users          : {users['total']}
⚠️   Unresolved Anomalies  : {anomalies['total']}
🍽️   Active Diet Plans     : {diet_plans['total']}
💪  Training Sessions     : {training['total']}
🏢  Total Vendors         : {vendors['total']}
{'═' * 80}
        """.strip()

    except Exception as e:
        return f"Dashboard query failed: {str(e)}"


# ── Run Server ───────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import uvicorn
    import inspect

    print("SIGNATURE:")
    print(inspect.signature(mcp.streamable_http_app))

    app = mcp.streamable_http_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )