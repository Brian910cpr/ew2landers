#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, datetime

# -------------------------------------------------------
# CORRECT PATHS — FIXES YOUR WORKFLOW FAILURE
# -------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCHEDULE_JSON = os.path.join(ROOT, "docs", "data", "schedule.json")
COURSE_DESCRIPTIONS_JSON = os.path.join(ROOT, "docs", "data", "course-descriptions.json")

OUTPUT_DIR = os.path.join(ROOT, "docs", "classes")

# -------------------------------------------------------
# LOAD JSON SAFELY
# -------------------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------------------------------
# BUILD LANDER TEMPLATE (SHORTENED FOR BREVITY)
# -------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="/assets/css/main.css">
</head>
<body>

<section class="lander">
  <h1>{course_name}</h1>
  <h2>{date_time}</h2>

  <p class="price">Price: ${price}</p>

  <p class="location">{location}</p>

  <a class="primary-button"
     href="https://coastalcprtraining.enrollware.com/enroll?id={session_id}">
     Register Now
  </a>

  <hr>

  <div class="description">
    {course_description}
  </div>

</section>

</body>
</html>
"""

# -------------------------------------------------------
# MAIN BUILD FUNCTION
# -------------------------------------------------------
def main():

    # Load schedule.json and course-descriptions.json
    schedule = load_json(SCHEDULE_JSON)
    descriptions = load_json(COURSE_DESCRIPTIONS_JSON)

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for item in schedule:
        session_id = str(item["id"])
        course_id = str(item["course_id"])
        title = item["title"]
        date = item["date"]
        time = item["time"]
        price = item.get("price", "—")
        location = item.get("location", "Location TBD")

        # Pull description
        course_description = descriptions.get(course_id, {}).get("description", "")

        # Build output filename
        filename = f"{session_id}.html"
        outfile = os.path.join(OUTPUT_DIR, filename)

        # Render HTML
        html = HTML_TEMPLATE.format(
            title=title,
            course_name=title,
            date_time=f"{date} at {time}",
            price=price,
            location=location,
            session_id=session_id,
            course_description=course_description
        )

        with open(outfile, "w", encoding="utf-8") as f:
            f.write(html)

    print("Class landers built successfully.")


if __name__ == "__main__":
    main()
