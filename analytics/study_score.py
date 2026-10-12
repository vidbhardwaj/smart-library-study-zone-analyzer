"""
Smart Library Study Zone Analyzer - Study Environment Scoring Algorithm
Calculates comfort, focus suitability, and study environment quality scores
based on environmental sensor inputs (temperature, humidity, light, noise, occupancy).
"""

from typing import Dict, Any, List


def calculate_study_score(
    temp: float,
    humidity: float,
    light: float,
    noise: float,
    occupancy: int = 0,
    capacity: int = 10
) -> Dict[str, Any]:
    """
    Calculates the overall study environment score (0-100) and sub-scores.

    Parameters:
        temp (float): Temperature in Celsius (°C). Ideal: 21°C - 24°C.
        humidity (float): Relative humidity percentage (%). Ideal: 40% - 60%.
        light (float): Illuminance in Lux (or calibrated 0-100 scale). Ideal: 300 - 500 Lux.
        noise (float): Sound level in decibels (dB or calibrated 0-100). Ideal: < 45 dB.
        occupancy (int): Current count of people inside the zone.
        capacity (int): Maximum zone seating capacity.

    Returns:
        dict: Overall score, sub-scores, rating label, color, and actionable recommendations.
    """
    recommendations: List[str] = []

    # 1. Thermal Comfort Score (Weight: 25%)
    # ASHRAE Standard 55: Optimal indoor study temperature ~22°C (range 20-25°C), RH 40-60%
    temp_score = 100.0
    if 21.0 <= temp <= 24.5:
        temp_score = 100.0
    elif 19.0 <= temp < 21.0 or 24.5 < temp <= 27.0:
        deviation = abs(temp - 22.5)
        temp_score = max(50.0, 100.0 - (deviation * 12.0))
        if temp < 21.0:
            recommendations.append("Temperature is slightly cool; consider adjusting HVAC.")
        else:
            recommendations.append("Temperature is slightly warm; ventilation recommended.")
    else:
        deviation = abs(temp - 22.5)
        temp_score = max(10.0, 100.0 - (deviation * 16.0))
        if temp < 19.0:
            recommendations.append("Zone is too cold for prolonged focus.")
        else:
            recommendations.append("Zone is uncomfortably hot; cooling required.")

    hum_score = 100.0
    if 40.0 <= humidity <= 60.0:
        hum_score = 100.0
    elif 30.0 <= humidity < 40.0 or 60.0 < humidity <= 70.0:
        hum_score = 80.0
    else:
        hum_score = max(20.0, 100.0 - abs(humidity - 50.0) * 2.0)
        if humidity > 70.0:
            recommendations.append("High humidity detected; dehumidification advised.")

    thermal_score = (temp_score * 0.65) + (hum_score * 0.35)

    # 2. Acoustic Comfort Score (Weight: 35%)
    # Libraries standard: Quiet reading < 40-45 dB, Moderate 45-60 dB, Loud > 65 dB
    if noise <= 42.0:
        acoustic_score = 100.0
    elif noise <= 55.0:
        # Linear drop from 100 to 75
        acoustic_score = 100.0 - ((noise - 42.0) / 13.0) * 25.0
    elif noise <= 70.0:
        # Moderate distraction: drops to 40
        acoustic_score = 75.0 - ((noise - 55.0) / 15.0) * 35.0
        recommendations.append("Moderate ambient noise; noise cancellation headphones recommended.")
    else:
        # Severe distraction
        acoustic_score = max(5.0, 40.0 - ((noise - 70.0) * 1.5))
        recommendations.append("High noise level! Not suitable for quiet study. Zone rules enforcement needed.")

    # 3. Visual / Lighting Comfort Score (Weight: 25%)
    # IESNA / CIBSE Standards: Reading/Writing ~300 - 500 Lux (or 50-80 on normalized 0-100 scale)
    # The sensor input can be raw Lux (0-2000) or normalized level (0-100)
    effective_light = light
    if light > 150.0:
        # Raw lux scale
        if 350.0 <= light <= 600.0:
            visual_score = 100.0
        elif 250.0 <= light < 350.0:
            visual_score = 85.0
            recommendations.append("Lighting is soft; task reading lamp suggested.")
        elif light < 250.0:
            visual_score = max(20.0, (light / 250.0) * 70.0)
            recommendations.append("Dim lighting detected; increase illumination for study.")
        elif 600.0 < light <= 900.0:
            visual_score = 80.0
        else:
            visual_score = max(30.0, 100.0 - ((light - 900.0) / 20.0))
            recommendations.append("Glare or excessive lighting detected.")
    else:
        # Normalized 0-100 sensor scale
        if 50.0 <= light <= 85.0:
            visual_score = 100.0
        elif 35.0 <= light < 50.0:
            visual_score = 80.0
            recommendations.append("Lighting slightly dim; adjust desk lamp.")
        elif light < 35.0:
            visual_score = max(20.0, (light / 35.0) * 65.0)
            recommendations.append("Insufficient light for reading; turn on lights.")
        else:
            visual_score = 90.0

    # 4. Occupancy Comfort Score (Weight: 15%)
    cap = max(1, capacity)
    occ_ratio = min(1.0, max(0.0, occupancy / cap))
    if occ_ratio <= 0.60:
        occupancy_score = 100.0
    elif occ_ratio <= 0.85:
        occupancy_score = 85.0
    elif occ_ratio < 1.0:
        occupancy_score = 65.0
        recommendations.append("Zone near capacity; limited seats available.")
    else:
        occupancy_score = 40.0
        recommendations.append("Zone is at FULL capacity! Seek alternative zones.")

    # Weighted Overall Score Calculation
    raw_score = (
        (acoustic_score * 0.35) +
        (thermal_score * 0.25) +
        (visual_score * 0.25) +
        (occupancy_score * 0.15)
    )
    overall_score = int(round(max(0.0, min(100.0, raw_score))))

    # Rating categorization
    if overall_score >= 88:
        rating = "Optimal Study Zone"
        color = "#10b981"  # Emerald green
        status_badge = "Excellent"
    elif overall_score >= 75:
        rating = "Good Study Zone"
        color = "#3b82f6"  # Royal blue
        status_badge = "Good"
    elif overall_score >= 60:
        rating = "Moderate Conditions"
        color = "#f59e0b"  # Amber
        status_badge = "Moderate"
    elif overall_score >= 45:
        rating = "Suboptimal Study Zone"
        color = "#f97316"  # Orange
        status_badge = "Suboptimal"
    else:
        rating = "Poor / Distracting"
        color = "#ef4444"  # Red
        status_badge = "Distracting"

    if not recommendations:
        recommendations.append("Environmental conditions are optimal for focused study.")

    return {
        "overall_score": overall_score,
        "rating": rating,
        "status_badge": status_badge,
        "color": color,
        "sub_scores": {
            "acoustic": round(acoustic_score, 1),
            "thermal": round(thermal_score, 1),
            "visual": round(visual_score, 1),
            "occupancy": round(occupancy_score, 1),
        },
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    # Test sample readings
    test_result = calculate_study_score(temp=23.4, humidity=52.0, light=420.0, noise=38.5, occupancy=1, capacity=4)
    print("Test Calculation Output:")
    for k, v in test_result.items():
        print(f"  {k}: {v}")
