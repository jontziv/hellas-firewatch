# Product Requirements (MVP)

## Goal
Help people in Greece quickly validate satellite wildfire detections with community feedback, while remaining responsible.

## MVP Features
1. Live map of detections (last 24h, filter by confidence)
2. Verify prompt for nearby users (confirm / deny / unsure + optional photo)
3. Community status banner per detection (counts)
4. Risk overlay (placeholder FWI buckets) + wind direction arrow
5. Responsible link-out panel to official sources and emergency numbers

## North-star metric
- % of detections that receive ≥ 3 verifications within 30 minutes.

## Guardrails
- False-alarm rate (verified “no fire”)
- Report abuse rate (basic: rate-limits + duplicate vote blocking + cooldown)
