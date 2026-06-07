from datetime import datetime

from app.services.database import db_execute, db_fetchall, db_fetchone, db_insert_returning_id, get_connection, json_dump, json_load


def create_claim(user_id: int, file_name: str, payload: dict) -> dict:
    claim_number = f"CLM-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    with get_connection() as conn:
        claim_id = db_insert_returning_id(
            conn,
            """
            INSERT INTO claims (
                claim_number, user_id, file_name, vehicle_segment, workshop_type, car_model, damage_category, severity,
                severity_score, estimated_cost_min, estimated_cost_max, estimated_cost_range,
                damage_detected, num_damages, damage_area_ratio, damage_types, detections,
                preprocessing, cost_breakdown, model, annotated_image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_number,
                user_id,
                file_name,
                payload["cost_breakdown"].get("vehicle_segment", "sedan"),
                payload["cost_breakdown"].get("workshop_type", "standard"),
                payload["cost_breakdown"].get("car_model", "maruti_swift"),
                payload["cost_breakdown"].get("damage_category_resolved", payload["cost_breakdown"].get("damage_category", "auto")),
                payload["severity"],
                payload["severity_score"],
                payload["estimated_cost_min"],
                payload["estimated_cost_max"],
                payload["estimated_cost_range"],
                int(payload["damage_detected"]),
                payload["num_damages"],
                payload["damage_area_ratio"],
                json_dump(payload["damage_types"]),
                json_dump(payload["detections"]),
                json_dump(payload["preprocessing"]),
                json_dump(payload["cost_breakdown"]),
                json_dump(payload["model"]),
                payload["annotated_image"],
            ),
        )
    return get_claim(user_id, claim_id)


def list_claims(user: dict) -> list[dict]:
    query = """
        SELECT id, claim_number, file_name, vehicle_segment, workshop_type, car_model, damage_category, status, severity,
               severity_score, estimated_cost_min, estimated_cost_max, estimated_cost_range,
               damage_detected, num_damages, damage_area_ratio, damage_types, created_at
        FROM claims
    """
    params = ()
    if user["role"] != "admin":
        query += " WHERE user_id = ?"
        params = (user["id"],)
    query += " ORDER BY created_at DESC"

    with get_connection() as conn:
        rows = db_fetchall(conn, query, params)

    claims = []
    for row in rows:
        item = row
        item["damage_detected"] = bool(item["damage_detected"])
        item["damage_types"] = json_load(item["damage_types"])
        claims.append(item)
    return claims


def get_claim(user_id: int, claim_id: int, allow_any: bool = False) -> dict | None:
    query = "SELECT * FROM claims WHERE id = ?"
    params = [claim_id]
    if not allow_any:
        query += " AND user_id = ?"
        params.append(user_id)

    with get_connection() as conn:
        claim = db_fetchone(conn, query, tuple(params))
    if not claim:
        return None

    for key in ["damage_types", "detections", "preprocessing", "cost_breakdown", "model"]:
        claim[key] = json_load(claim[key])
    claim["damage_detected"] = bool(claim["damage_detected"])
    return claim


def update_claim_status(user: dict, claim_id: int, status: str) -> dict | None:
    if user["role"] not in ["admin", "surveyor"]:
        return None
    allowed = {"AI Assessed", "Needs Review", "Approved", "Rejected"}
    if status not in allowed:
        status = "Needs Review"
    with get_connection() as conn:
        db_execute(conn, "UPDATE claims SET status = ? WHERE id = ?", (status, claim_id))
    return get_claim(user["id"], claim_id, allow_any=True)
