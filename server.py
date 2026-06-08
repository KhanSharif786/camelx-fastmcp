import os
import time
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

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

def run_query(sql: str, params=None) -> tuple[list[dict], float]:
    """Execute a SQL query and return (rows, elapsed_ms)."""
    conn = get_connection()
    start = time.time()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or [])
            rows = [dict(row) for row in cur.fetchall()]
        elapsed = round((time.time() - start) * 1000, 1)
        return rows, elapsed
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

# ── Language Detection ───────────────────────────────────────
def is_arabic(text: str) -> bool:
    """Detect if text contains Arabic characters."""
    return any('\u0600' <= c <= '\u06FF' for c in text)

# ── Reference Footer ─────────────────────────────────────────
def make_reference(tool_name: str, table_names: list[str], elapsed_ms: float, lang: str = "en") -> str:
    """Generate a reference footer for tool responses."""
    tables = ", ".join(table_names)
    if lang == "ar":
        return (
            f"\n\n{'─' * 60}\n"
            f"📎 **المرجع**\n"
            f"  • الأداة المستخدمة : `{tool_name}`\n"
            f"  • الجداول المستعملة: `{tables}`\n"
            f"  • وقت الاستجابة   : {elapsed_ms} ms\n"
            f"  • مصدر البيانات   : CamelX — Azure PostgreSQL\n"
            f"{'─' * 60}"
        )
    return (
        f"\n\n{'─' * 60}\n"
        f"📎 **Reference**\n"
        f"  • Tool Used    : `{tool_name}`\n"
        f"  • Table(s)     : `{tables}`\n"
        f"  • Response Time: {elapsed_ms} ms\n"
        f"  • Data Source  : CamelX — Azure PostgreSQL\n"
        f"{'─' * 60}"
    )


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

════════════════════════════════════════════════════════
MULTILINGUAL SUPPORT
════════════════════════════════════════════════════════

RULE — LANGUAGE DETECTION & RESPONSE
You MUST detect the language of the user's question and reply
in the SAME language.

If the question is in ARABIC:
  → Reply ENTIRELY in Arabic
  → Use Arabic numerals and formatting
  → Example: "كم عدد الجمال؟" → Answer in Arabic

If the question is in ENGLISH:
  → Reply in English as normal

Arabic translations for common terms:
  جمل / جمال = Camel / Camels
  السلالة = Breed
  الجنس = Gender
  ذكر = Male
  أنثى = Female
  معدل ضربات القلب = Heart Rate
  درجة الحرارة = Temperature
  التدريب = Training
  السباق = Race
  التنبيهات = Alerts
  الأجهزة = Devices
  الأداء = Performance
  الصحة = Health

════════════════════════════════════════════════════════
REFERENCE — ALWAYS ADD AT THE END
════════════════════════════════════════════════════════

RULE — EVERY RESPONSE MUST END WITH A REFERENCE BLOCK
After every answer, always include a reference section showing:
  • Which MCP Tool was called
  • Which database table(s) were queried
  • Response time
  • Data source

The reference is auto-generated by each tool — do NOT remove it.
""",
transport_security=TransportSecuritySettings(
    allowed_hosts=["camelx-api-v2.onrender.com"]
)
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
            rows, elapsed = run_query("SELECT COUNT(*) as total_camels FROM camels")

        elif stat_type == "by_breed":
            rows, elapsed = run_query(
                "SELECT breed, COUNT(*) as count FROM camels "
                "GROUP BY breed ORDER BY count DESC"
            )

        elif stat_type == "by_gender":
            rows, elapsed = run_query(
                "SELECT gender, COUNT(*) as count FROM camels GROUP BY gender"
            )

        elif stat_type == "by_status":
            rows, elapsed = run_query(
                "SELECT status, COUNT(*) as count FROM camels GROUP BY status"
            )

        elif stat_type == "top_performers":
            rows, elapsed = run_query(
                "SELECT name, breed, gender, performance_index, health_index, fatigue_score "
                "FROM camels WHERE performance_index IS NOT NULL "
                "ORDER BY performance_index DESC LIMIT %s", [limit]
            )

        elif stat_type == "healthiest":
            rows, elapsed = run_query(
                "SELECT name, breed, health_index, performance_index, fatigue_score "
                "FROM camels WHERE health_index IS NOT NULL "
                "ORDER BY health_index DESC LIMIT %s", [limit]
            )

        elif stat_type == "most_fatigued":
            rows, elapsed = run_query(
                "SELECT name, breed, fatigue_score, health_index, performance_index "
                "FROM camels WHERE fatigue_score IS NOT NULL "
                "ORDER BY fatigue_score DESC LIMIT %s", [limit]
            )

        elif stat_type == "by_age":
            rows, elapsed = run_query(
                "SELECT name, breed, age, gender, health_index "
                "FROM camels ORDER BY age DESC LIMIT %s", [limit]
            )

        elif stat_type == "by_weight":
            rows, elapsed = run_query(
                "SELECT name, breed, weight, height, age "
                "FROM camels WHERE weight IS NOT NULL "
                "ORDER BY weight DESC LIMIT %s", [limit]
            )

        elif stat_type == "search":
            if not camel_name:
                return "Please provide camel_name to search."
            rows, elapsed = run_query(
                "SELECT name, name_arabic, age, breed, gender, weight, height, "
                "status, performance_index, health_index, fatigue_score "
                "FROM camels WHERE LOWER(name) LIKE LOWER(%s) LIMIT %s",
                [f"%{camel_name}%", limit]
            )
        else:
            return f"Unknown stat_type: {stat_type}"

        ref = make_reference("get_camel_stats", ["camels"], elapsed)
        label = stat_type.replace('_', ' ').title()

        if is_arabic(camel_name or stat_type):
            return f"إحصائيات الجمال — {label}\n{'═' * 80}\n{format_rows(rows)}{ref}"
        return f"Camel Stats — {label}\n{'═' * 80}\n{format_rows(rows)}{ref}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 2 — HEALTH METRICS
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_health_metrics(
    metric_type: str = "summary",
    hours: int = 0
) -> str:
    """
    Get health and vitals data for camels from IoT sensors.

    IMPORTANT — Time Period:
    - hours=0 means ALL available data (default)
    - 1 day=24, 7 days=168, 15 days=360, 1 month=720, 3 months=2160, 6 months=4320

    Args:
        metric_type: Options: summary, heart_rate, spo2, temperature, stress, blood_pressure, fatigue
        hours: Hours to look back. 0 = all available data (default)
    """
    try:
        if hours and hours > 0:
            time_filter = f"AND recorded_at > NOW() - INTERVAL '{hours} hours'"
            period_label = f"Last {hours} hours"
        else:
            time_filter = ""
            period_label = "All Time"

        if metric_type == "summary":
            rows, elapsed = run_query(
                f"""SELECT
                    ROUND(AVG(heart_rate)::numeric,1) as avg_heart_rate,
                    ROUND(AVG(spo2)::numeric,1) as avg_spo2,
                    ROUND(AVG(temperature)::numeric,1) as avg_temperature,
                    ROUND(AVG(stress)::numeric,1) as avg_stress,
                    ROUND(AVG(fatigue)::numeric,1) as avg_fatigue,
                    ROUND(AVG(blood_pressure_sbp)::numeric,1) as avg_systolic_bp,
                    COUNT(*) as total_readings
                FROM health_metrics
                WHERE 1=1 {time_filter}"""
            )

        elif metric_type == "heart_rate":
            rows, elapsed = run_query(
                f"""SELECT
                    ROUND(AVG(heart_rate)::numeric,1) as avg,
                    ROUND(MIN(heart_rate)::numeric,1) as min,
                    ROUND(MAX(heart_rate)::numeric,1) as max,
                    COUNT(*) as readings
                FROM health_metrics
                WHERE heart_rate IS NOT NULL
                {time_filter}"""
            )

        elif metric_type == "spo2":
            rows, elapsed = run_query(
                f"""SELECT
                    ROUND(AVG(spo2)::numeric,1) as avg_spo2,
                    ROUND(MIN(spo2)::numeric,1) as min_spo2,
                    ROUND(MAX(spo2)::numeric,1) as max_spo2
                FROM health_metrics
                WHERE spo2 IS NOT NULL
                {time_filter}"""
            )

        elif metric_type == "temperature":
            rows, elapsed = run_query(
                f"""SELECT
                    ROUND(AVG(temperature)::numeric,1) as avg_temp,
                    ROUND(MIN(temperature)::numeric,1) as min_temp,
                    ROUND(MAX(temperature)::numeric,1) as max_temp
                FROM health_metrics
                WHERE temperature IS NOT NULL
                {time_filter}"""
            )

        elif metric_type == "stress":
            rows, elapsed = run_query(
                f"""SELECT
                    ROUND(AVG(stress)::numeric,2) as avg_stress,
                    ROUND(MAX(stress)::numeric,2) as max_stress,
                    COUNT(CASE WHEN stress > 0.7 THEN 1 END) as high_stress_count
                FROM health_metrics
                WHERE stress IS NOT NULL
                {time_filter}"""
            )

        elif metric_type == "blood_pressure":
            rows, elapsed = run_query(
                f"""SELECT
                    ROUND(AVG(blood_pressure_sbp)::numeric,1) as avg_systolic,
                    ROUND(AVG(blood_pressure_dbp)::numeric,1) as avg_diastolic,
                    ROUND(MAX(blood_pressure_sbp)::numeric,1) as max_systolic
                FROM health_metrics
                WHERE blood_pressure_sbp IS NOT NULL
                {time_filter}"""
            )

        elif metric_type == "fatigue":
            rows, elapsed = run_query(
                f"""SELECT
                    ROUND(AVG(fatigue)::numeric,2) as avg_fatigue,
                    ROUND(MAX(fatigue)::numeric,2) as max_fatigue,
                    COUNT(CASE WHEN fatigue > 0.7 THEN 1 END) as high_fatigue_count
                FROM health_metrics
                WHERE fatigue IS NOT NULL
                {time_filter}"""
            )
        else:
            return f"Unknown metric_type: {metric_type}"

        lang = "ar" if is_arabic(metric_type) else "en"
        ref = make_reference("get_health_metrics", ["health_metrics"], elapsed, lang)
        label = metric_type.replace('_',' ').title()
        if lang == "ar":
            period_ar = "كل الوقت" if hours == 0 else f"آخر {hours} ساعة"
            return f"مقاييس الصحة — {label} ({period_ar})\n{'═'*80}\n{format_rows(rows)}{ref}"
        return f"Health Metrics — {label} ({period_label})\n{'═'*80}\n{format_rows(rows)}{ref}"

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
            rows, elapsed = run_query(
                "SELECT name, location, race_date, distance, "
                "category, age_category, max_participants, prize_pool "
                "FROM races WHERE race_date > NOW() "
                "ORDER BY race_date ASC LIMIT %s", [limit]
            )

        elif query_type == "results":
            rows, elapsed = run_query(
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
            rows, elapsed = run_query(
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
            rows, elapsed = run_query(
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

        lang = "ar" if is_arabic(query_type) else "en"
        ref = make_reference("get_race_data", ["races", "race_results", "camels"], elapsed, lang)
        if lang == "ar":
            return f"بيانات السباق — {query_type.title()}\n{'═'*80}\n{format_rows(rows)}{ref}"
        return f"Race Data — {query_type.title()}\n{'═'*80}\n{format_rows(rows)}{ref}"

    except Exception as e:
        return f"Query failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# TOOL 4 — TRAINING ANALYTICS
# ════════════════════════════════════════════════════════════
@mcp.tool()
def get_training_data(
    query_type: str = "summary",
    limit: int = 10,
    days: int = 0
) -> str:
    """
    Get training session data and performance logs from CamelX.
    Use for questions about training sessions, distances covered,
    calories burned, speed, or top training performers.

    IMPORTANT — Time Period Handling:
    - days=0 means all available data (default)
    - Convert: 1 week=7, 1 month=30, 3 months=90, 6 months=180

    NOTE: training_events table has the actual scheduled sessions (50 records).
    training_logs has per-camel performance logs linked to sessions.

    Args:
        query_type: Type of training data. Options:
            "summary"    — overall training stats from both tables
            "top_camels" — camels with best training performance
            "recent"     — recent training events
            "events"     — list all training events
        limit: Number of records (default 10)
        days: Days to look back. 0 = all available data (default)
    """
    try:
        if days and days > 0:
            te_filter = f"AND te.scheduled_date > NOW() - INTERVAL '{days} days'"
            tl_filter = f"AND tl.recorded_at > NOW() - INTERVAL '{days} days'"
            tl_basic  = f"WHERE recorded_at > NOW() - INTERVAL '{days} days'"
            te_basic  = f"WHERE scheduled_date > NOW() - INTERVAL '{days} days'"
            period_label = f"Last {days} days"
        else:
            te_filter = ""
            tl_filter = ""
            tl_basic  = ""
            te_basic  = ""
            period_label = "All Time"

        if query_type == "summary":
            # Events summary from training_events
            ev_rows, ev_elapsed = run_query(
                f"""SELECT
                    COUNT(*) as total_training_events,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled,
                    ROUND(AVG(distance)::numeric,1) as avg_distance_km,
                    ROUND(AVG(duration)::numeric,0) as avg_duration_min
                FROM training_events
                {te_basic}"""
            )
            # Performance logs from training_logs
            lg_rows, elapsed = run_query(
                f"""SELECT
                    COUNT(*) as total_performance_logs,
                    ROUND(AVG(actual_distance)::numeric,1) as avg_actual_distance_km,
                    ROUND(AVG(average_speed)::numeric,1) as avg_speed_kmh,
                    SUM(calories_burned) as total_calories_burned,
                    ROUND(AVG(CAST(performance_rating AS numeric)),1) as avg_performance_rating
                FROM training_logs
                {tl_basic}"""
            )
            ref = make_reference("get_training_data", ["training_events", "training_logs"], elapsed)
            return (
                f"Training Summary ({period_label})\n{'═'*80}\n"
                f"Training Events:\n{format_rows(ev_rows)}\n\n"
                f"Performance Logs:\n{format_rows(lg_rows)}{ref}"
            )

        elif query_type == "top_camels":
            rows, elapsed = run_query(
                f"""SELECT c.name as camel_name,
                    COUNT(tl.id) as log_entries,
                    ROUND(AVG(tl.average_speed)::numeric,1) as avg_speed_kmh,
                    ROUND(SUM(tl.actual_distance)::numeric,1) as total_distance_km,
                    SUM(tl.calories_burned) as total_calories,
                    ROUND(AVG(CAST(tl.performance_rating AS numeric)),1) as avg_rating
                FROM training_logs tl
                JOIN camels c ON c.id = tl.camel_id
                WHERE 1=1 {tl_filter}
                GROUP BY c.name
                ORDER BY avg_rating DESC NULLS LAST
                LIMIT %s""", [limit]
            )

        elif query_type == "recent":
            rows, elapsed = run_query(
                f"""SELECT
                    te.title, te.session_type, te.status,
                    te.intensity, te.distance, te.duration,
                    te.scheduled_date, te.completed_at
                FROM training_events te
                WHERE 1=1 {te_filter}
                ORDER BY te.scheduled_date DESC
                LIMIT %s""", [limit]
            )

        elif query_type == "events":
            rows, elapsed = run_query(
                f"""SELECT
                    te.title, te.session_type, te.status,
                    te.intensity, te.distance, te.duration,
                    te.scheduled_date
                FROM training_events te
                WHERE 1=1 {te_filter}
                ORDER BY te.scheduled_date DESC
                LIMIT %s""", [limit]
            )
        else:
            return f"Unknown query_type: {query_type}"

        ref = make_reference("get_training_data", ["training_events", "training_logs", "camels"], elapsed)
        label = query_type.replace('_',' ').title()
        return f"Training Data — {label} ({period_label})\n{'═'*80}\n{format_rows(rows)}{ref}"

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
        ref_tables = ["alerts", "camels", "anomaly_detections"]
        import time as _time

        if query_type == "active_alerts":
            t0 = _time.time()
            total, _ = run_query("SELECT COUNT(*) as total FROM alerts WHERE status = 'active'")
            by_severity, _ = run_query(
                "SELECT severity, COUNT(*) as count FROM alerts "
                "WHERE status = 'active' GROUP BY severity ORDER BY count DESC"
            )
            elapsed = round((_time.time() - t0) * 1000, 1)
            ref = make_reference("get_alerts_and_anomalies", ref_tables, elapsed)
            return (
                f"Active Alerts Summary\n{'═'*80}\n"
                f"Total Active: {total[0]['total']}\n\n"
                f"By Severity:\n{format_rows(by_severity)}{ref}"
            )

        elif query_type == "critical_alerts":
            rows, elapsed = run_query(
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
            rows, elapsed = run_query(
                """SELECT a.title, a.severity, a.alert_type,
                    a.status, a.created_at, c.name as camel_name
                FROM alerts a
                LEFT JOIN camels c ON c.id = a.camel_id
                ORDER BY a.created_at DESC
                LIMIT %s""", [limit]
            )

        elif query_type == "anomalies":
            t0 = _time.time()
            total, _ = run_query(
                "SELECT COUNT(*) as total FROM anomaly_detections WHERE resolved = false"
            )
            by_severity, _ = run_query(
                "SELECT severity, metric_name, COUNT(*) as count "
                "FROM anomaly_detections WHERE resolved = false "
                "GROUP BY severity, metric_name ORDER BY count DESC LIMIT %s", [limit]
            )
            elapsed = round((_time.time() - t0) * 1000, 1)
            ref = make_reference("get_alerts_and_anomalies", ref_tables, elapsed)
            return (
                f"Unresolved Anomalies\n{'═'*80}\n"
                f"Total Unresolved: {total[0]['total']}\n\n"
                f"By Severity & Metric:\n{format_rows(by_severity)}{ref}"
            )
        else:
            return f"Unknown query_type: {query_type}"

        ref = make_reference("get_alerts_and_anomalies", ref_tables, elapsed)
        label = query_type.replace('_',' ').title()
        return f"Alerts — {label}\n{'═'*80}\n{format_rows(rows)}{ref}"

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
        import time as _time
        if query_type == "summary":
            t0 = _time.time()
            total, _ = run_query("SELECT COUNT(*) as total_devices FROM iot_devices")
            by_type, _ = run_query(
                "SELECT device_type, COUNT(*) as count FROM iot_devices GROUP BY device_type"
            )
            battery, _ = run_query(
                """SELECT
                    ROUND(AVG(battery_level)::numeric,1) as avg_battery,
                    COUNT(CASE WHEN battery_level < 20 THEN 1 END) as low_battery_devices,
                    COUNT(CASE WHEN battery_level >= 80 THEN 1 END) as healthy_battery_devices
                FROM iot_devices WHERE battery_level IS NOT NULL"""
            )
            elapsed = round((_time.time() - t0) * 1000, 1)
            ref = make_reference("get_iot_devices", ["iot_devices", "camels"], elapsed)
            return (
                f"IoT Devices Summary\n{'═'*80}\n"
                f"Total Devices: {total[0]['total_devices']}\n\n"
                f"By Type:\n{format_rows(by_type)}\n\n"
                f"Battery Status:\n{format_rows(battery)}{ref}"
            )

        elif query_type == "low_battery":
            rows, elapsed = run_query(
                """SELECT d.device_id, d.device_type, d.battery_level,
                    c.name as camel_name, d.last_sync_at
                FROM iot_devices d
                LEFT JOIN camels c ON c.id = d.camel_id
                WHERE d.battery_level < 20
                ORDER BY d.battery_level ASC"""
            )

        elif query_type == "by_type":
            rows, elapsed = run_query(
                "SELECT device_type, COUNT(*) as count, "
                "ROUND(AVG(battery_level)::numeric,1) as avg_battery "
                "FROM iot_devices GROUP BY device_type"
            )
        else:
            return f"Unknown query_type: {query_type}"

        ref = make_reference("get_iot_devices", ["iot_devices", "camels"], elapsed)
        label = query_type.replace('_',' ').title()
        return f"IoT Devices — {label}\n{'═'*80}\n{format_rows(rows)}{ref}"

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

    NOTE: diet_plans uses 'status' column (values: active/inactive).
    diet_plan_camels links diet plans to camels.

    Args:
        query_type: Type of diet data. Options:
            "summary"      — all diet plans count and calorie stats
            "active_plans" — only active status plans
            "meals"        — recent meal details
            "camel_diets"  — which camels have diet plans assigned
    """
    try:
        if query_type == "summary":
            rows, elapsed = run_query(
                """SELECT
                    COUNT(*) as total_diet_plans,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_plans,
                    COUNT(CASE WHEN status != 'active' THEN 1 END) as inactive_plans,
                    ROUND(AVG(total_calories)::numeric,0) as avg_daily_calories,
                    SUM(total_calories) as total_calories_all_plans
                FROM diet_plans"""
            )

        elif query_type == "active_plans":
            rows, elapsed = run_query(
                """SELECT dp.name, dp.status, dp.total_calories,
                    dp.description, dp.created_at
                FROM diet_plans dp
                WHERE dp.status = 'active'
                ORDER BY dp.created_at DESC
                LIMIT 20"""
            )

        elif query_type == "meals":
            rows, elapsed = run_query(
                """SELECT m.meal_type, m.scheduled_time,
                    m.calories, m.protein, m.carbs, m.fats, m.water,
                    dp.name as diet_plan_name, dp.status
                FROM meals m
                JOIN diet_plans dp ON dp.id = m.diet_plan_id
                ORDER BY m.created_at DESC
                LIMIT 20"""
            )

        elif query_type == "camel_diets":
            rows, elapsed = run_query(
                """SELECT
                    c.name as camel_name, c.breed,
                    dp.name as diet_plan, dp.status,
                    dp.total_calories, dpc.assigned_at
                FROM diet_plan_camels dpc
                JOIN camels c ON c.id = dpc.camel_id
                JOIN diet_plans dp ON dp.id = dpc.diet_plan_id
                ORDER BY dpc.assigned_at DESC
                LIMIT 20"""
            )
        else:
            return f"Unknown query_type: {query_type}"

        ref = make_reference("get_diet_info", ["diet_plans", "meals", "diet_plan_camels"], elapsed)
        return f"Diet & Nutrition — {query_type.title()}\n{'═'*80}\n{format_rows(rows)}{ref}"

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
            rows, elapsed = run_query(
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
            rows, elapsed = run_query(
                """SELECT r.name as role_name, COUNT(u.id) as user_count
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE u.is_active = true
                GROUP BY r.name
                ORDER BY user_count DESC"""
            )

        elif query_type == "user_total":
            rows, elapsed = run_query(
                "SELECT COUNT(*) as total_active_users FROM users WHERE is_active = true"
            )
        else:
            return f"Unknown query_type: {query_type}"

        ref = make_reference("get_vendor_and_user_info", ["vendors", "users", "roles"], elapsed)
        label = query_type.replace('_',' ').title()
        return f"Vendor & User Info — {label}\n{'═'*80}\n{format_rows(rows)}{ref}"

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
        import time as _time
        t0 = _time.time()
        camels,    _ = run_query("SELECT COUNT(*) as total FROM camels")
        devices,   _ = run_query("SELECT COUNT(*) as total FROM iot_devices")
        alerts,    _ = run_query("SELECT COUNT(*) as total FROM alerts WHERE status = 'active'")
        upcoming,  _ = run_query("SELECT COUNT(*) as total FROM races WHERE race_date > NOW()")
        users,     _ = run_query("SELECT COUNT(*) as total FROM users WHERE is_active = true")
        anomalies, _ = run_query("SELECT COUNT(*) as total FROM anomaly_detections WHERE resolved = false")
        diet_plans,_ = run_query("SELECT COUNT(*) as total FROM diet_plans WHERE status = 'active'")
        training,  _ = run_query("SELECT COUNT(*) as total FROM training_events")
        vendors,   _ = run_query("SELECT COUNT(*) as total FROM vendors")
        elapsed = round((_time.time() - t0) * 1000, 1)

        all_tables = "camels, iot_devices, alerts, races, users, anomaly_detections, diet_plans, training_logs, vendors"
        ref = make_reference("get_dashboard_overview", [all_tables], elapsed)

        return f"""
CamelX Dashboard Overview
{'═' * 80}
🐪  Total Camels          : {camels[0]['total']}
📡  IoT Devices           : {devices[0]['total']}
🚨  Active Alerts         : {alerts[0]['total']}
🏁  Upcoming Races        : {upcoming[0]['total']}
👥  Active Users          : {users[0]['total']}
⚠️   Unresolved Anomalies  : {anomalies[0]['total']}
🍽️   Active Diet Plans     : {diet_plans[0]['total']}
💪  Training Sessions     : {training[0]['total']}
🏢  Total Vendors         : {vendors[0]['total']}
{'═' * 80}
{ref}
        """.strip()

    except Exception as e:
        return f"Dashboard query failed: {str(e)}"


# ── Run Server ───────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import uvicorn

    app = mcp.streamable_http_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        forwarded_allow_ips="*",
        proxy_headers=True
    )