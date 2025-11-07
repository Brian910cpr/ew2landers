#!/usr/bin/env python3
import json, sys

p = json.load(open("docs/data/pivot.json","r",encoding="utf-8"))

# Test 1: structure present
assert "sections" in p and isinstance(p["sections"], list)
assert "courses"  in p and isinstance(p["courses"], list)
assert "sessions" in p and isinstance(p["sessions"], list)

# Test 2: every session.course_id exists in courses
course_ids = {c["id"] for c in p["courses"]}
for s in p["sessions"]:
    assert s["course_id"] in course_ids, f"Session {s.get('id')} has unknown course_id {s.get('course_id')}"

# Test 3: ordering indices monotonic non-negative
for i, sec in enumerate(p["sections"]):
    assert sec["index"] == i, "Section index must match order"

print("pivot sanity tests passed")
