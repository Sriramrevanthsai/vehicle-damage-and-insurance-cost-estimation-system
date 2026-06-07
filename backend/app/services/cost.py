from collections import Counter


CAR_MODELS = {
    "maruti_swift": {"label": "Maruti Suzuki Swift", "segment": "hatchback", "multiplier": 0.85},
    "hyundai_i20": {"label": "Hyundai i20", "segment": "hatchback", "multiplier": 0.95},
    "tata_altroz": {"label": "Tata Altroz", "segment": "hatchback", "multiplier": 0.95},
    "maruti_baleno": {"label": "Maruti Suzuki Baleno", "segment": "hatchback", "multiplier": 0.92},
    "honda_amaze": {"label": "Honda Amaze", "segment": "sedan", "multiplier": 1.0},
    "hyundai_verna": {"label": "Hyundai Verna", "segment": "sedan", "multiplier": 1.12},
    "honda_city": {"label": "Honda City", "segment": "sedan", "multiplier": 1.18},
    "skoda_slavia": {"label": "Skoda Slavia", "segment": "sedan", "multiplier": 1.28},
    "tata_nexon": {"label": "Tata Nexon", "segment": "suv", "multiplier": 1.08},
    "hyundai_creta": {"label": "Hyundai Creta", "segment": "suv", "multiplier": 1.18},
    "kia_seltos": {"label": "Kia Seltos", "segment": "suv", "multiplier": 1.22},
    "mahindra_xuv700": {"label": "Mahindra XUV700", "segment": "suv", "multiplier": 1.35},
    "toyota_innova": {"label": "Toyota Innova Crysta", "segment": "suv", "multiplier": 1.38},
    "mg_hector": {"label": "MG Hector", "segment": "suv", "multiplier": 1.42},
    "jeep_compass": {"label": "Jeep Compass", "segment": "luxury", "multiplier": 1.65},
    "bmw_3_series": {"label": "BMW 3 Series", "segment": "luxury", "multiplier": 2.2},
    "mercedes_c_class": {"label": "Mercedes-Benz C-Class", "segment": "luxury", "multiplier": 2.35},
    "audi_a4": {"label": "Audi A4", "segment": "luxury", "multiplier": 2.3},
}

WORKSHOP_MULTIPLIERS = {
    "independent": 0.88,
    "standard": 1.0,
    "authorized": 1.22,
}

DAMAGE_CATEGORY_RULES = {
    "scratch": {"label": "Scratch", "base": (1500, 7000), "weight": 0.55, "cap": 16000},
    "paint_damage": {"label": "Paint damage", "base": (2500, 12000), "weight": 0.7, "cap": 24000},
    "dent": {"label": "Dent", "base": (4000, 18000), "weight": 0.9, "cap": 36000},
    "broken_glass": {"label": "Broken glass", "base": (5000, 30000), "weight": 1.0, "cap": 55000},
    "missing_part": {"label": "Missing part", "base": (7000, 45000), "weight": 1.15, "cap": 75000},
    "deformation": {"label": "Deformation", "base": (8000, 50000), "weight": 1.25, "cap": 85000},
}


def estimate_repair_cost(
    detections: list[dict],
    damage_area_ratio: float,
    vehicle_segment: str = "sedan",
    workshop_type: str = "standard",
    car_model: str = "maruti_swift",
    damage_category: str = "auto",
) -> dict:
    car_profile = CAR_MODELS.get(car_model, CAR_MODELS["maruti_swift"])
    vehicle_segment = car_profile.get("segment", vehicle_segment)
    workshop_type = workshop_type if workshop_type in WORKSHOP_MULTIPLIERS else "standard"

    if not detections:
        return {
            "severity": "None",
            "severity_score": 0,
            "estimated_cost_min": 0,
            "estimated_cost_max": 0,
            "estimated_cost_range": "INR 0",
            "currency": "INR",
            "car_model": car_model,
            "car_model_label": car_profile["label"],
            "damage_category": damage_category,
            "damage_category_label": "Auto from model",
            "vehicle_segment": vehicle_segment,
            "workshop_type": workshop_type,
            "review_required": False,
            "review_reason": "No visible damage was detected above the model threshold.",
            "assumptions": [
                "No damage was detected above the confidence threshold.",
                "A human surveyor should still inspect low-quality or partially visible images.",
            ],
            "line_items": [],
            "damage_mix": {},
        }

    selected_category = _selected_category(detections, damage_category)
    avg_confidence = sum(d["confidence"] for d in detections) / len(detections)
    class_weight = sum(_rule_for(_line_category(d, selected_category))["weight"] for d in detections) / len(detections)
    effective_area_ratio = min(damage_area_ratio, 0.045)
    severity_score = _severity_score(effective_area_ratio, avg_confidence, class_weight, len(detections))
    severity = _severity_label(severity_score)

    severity_multiplier = _severity_multiplier(severity_score)
    market_multiplier = car_profile["multiplier"] * WORKSHOP_MULTIPLIERS[workshop_type]
    count_multiplier = 1 + min(max(len(detections) - 1, 0) * 0.035, 0.12)

    min_total = 0
    max_total = 0
    line_items = []
    for detection in detections:
        category = _line_category(detection, selected_category)
        rule = _rule_for(category)
        effective_box_area = min(detection["area_ratio"], 0.02)
        area_multiplier = _area_multiplier(effective_box_area)
        confidence_multiplier = 0.9 + (detection["confidence"] * 0.14)
        low = rule["base"][0] * severity_multiplier * area_multiplier * market_multiplier * confidence_multiplier
        high = rule["base"][1] * severity_multiplier * area_multiplier * market_multiplier * confidence_multiplier
        low = min(low, rule["cap"] * 0.7 * market_multiplier)
        high = min(high, rule["cap"] * market_multiplier)
        min_total += low
        max_total += high
        line_items.append(
            {
                "damage_type": category,
                "damage_label": rule["label"],
                "model_detected_type": detection["damage_type"],
                "confidence": detection["confidence"],
                "area_ratio": detection["area_ratio"],
                "effective_area_ratio": round(effective_box_area, 5),
                "estimated_min": _round_to_500(low),
                "estimated_max": _round_to_500(high),
            }
        )

    category_rule = _rule_for(selected_category)
    claim_cap = _round_to_500(category_rule["cap"] * market_multiplier)
    min_total = _round_to_500(max(min_total * count_multiplier, 1000))
    max_total = _round_to_500(max(max_total * count_multiplier, min_total + 1500))
    max_total = min(max_total, claim_cap)
    min_total = min(min_total, max(1000, max_total - 3000))
    if max_total < min_total:
        max_total = min_total

    if selected_category in {"scratch", "paint_damage"} and severity in {"Major", "Severe"}:
        severity = "Moderate"
        severity_score = min(severity_score, 37)

    damage_counts = Counter(d["damage_type"] for d in detections)
    review_required = severity in ["Major", "Severe"] or avg_confidence < 0.45 or max_total > 90000
    assumptions = [
        "Estimate is a rule-based insurance support range, not a final claim approval.",
        "The estimator uses the six damage categories trained in the RT-DETR model.",
        f"Car model: {car_profile['label']}; damage category: {category_rule['label']}; workshop: {workshop_type}.",
        "Broad detector boxes are capped because one uploaded image cannot price hidden structural damage.",
        "Final production pricing should connect to insurer/OEM parts and labor-rate databases.",
    ]

    return {
        "severity": severity,
        "severity_score": round(severity_score, 2),
        "average_confidence": round(avg_confidence, 4),
        "review_required": review_required,
        "review_reason": _review_reason(severity, avg_confidence, max_total),
        "damage_mix": dict(damage_counts),
        "estimated_cost_min": min_total,
        "estimated_cost_max": max_total,
        "estimated_cost_range": f"INR {min_total:,} - INR {max_total:,}",
        "currency": "INR",
        "car_model": car_model,
        "car_model_label": car_profile["label"],
        "damage_category": damage_category,
        "damage_category_resolved": selected_category,
        "damage_category_label": category_rule["label"],
        "vehicle_segment": vehicle_segment,
        "workshop_type": workshop_type,
        "assumptions": assumptions,
        "line_items": line_items,
    }


def _selected_category(detections: list[dict], requested: str) -> str:
    if requested in DAMAGE_CATEGORY_RULES:
        return requested
    best = max(detections, key=lambda item: item.get("confidence", 0))
    detected = best.get("damage_type", "dent")
    return detected if detected in DAMAGE_CATEGORY_RULES else "dent"


def _line_category(detection: dict, selected_category: str) -> str:
    detected = detection.get("damage_type")
    return detected if detected in DAMAGE_CATEGORY_RULES else selected_category


def _rule_for(damage_type: str) -> dict:
    return DAMAGE_CATEGORY_RULES.get(damage_type, DAMAGE_CATEGORY_RULES["dent"])


def _severity_score(area_ratio: float, avg_confidence: float, class_weight: float, count: int) -> float:
    area_component = min(area_ratio * 650, 30)
    confidence_component = avg_confidence * 18
    class_component = min(class_weight * 10, 16)
    count_component = min(count * 2.5, 10)
    return min(area_component + confidence_component + class_component + count_component, 100)


def _severity_label(score: float) -> str:
    if score < 18:
        return "Minor"
    if score < 38:
        return "Moderate"
    if score < 62:
        return "Major"
    return "Severe"


def _severity_multiplier(score: float) -> float:
    if score < 18:
        return 0.72
    if score < 38:
        return 0.95
    if score < 62:
        return 1.15
    return 1.3


def _area_multiplier(area_ratio: float) -> float:
    if area_ratio < 0.004:
        return 0.7
    if area_ratio < 0.015:
        return 0.92
    return 1.05


def _review_reason(severity: str, avg_confidence: float, max_total: int) -> str:
    if avg_confidence < 0.45:
        return "Low model confidence requires manual surveyor review."
    if max_total > 90000:
        return "High estimate should be validated by a human surveyor."
    if severity in ["Major", "Severe"]:
        return "Major or severe visible damage requires manual review before approval."
    return "AI assessment can proceed as a low-risk estimate."


def _round_to_500(value: float) -> int:
    return int(round(value / 500.0) * 500)
