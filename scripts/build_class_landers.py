# scripts/build_class_landers.py

import json
from pathlib import Path
from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # Python < 3.9 fallback


def log(msg: str) -> None:
    print(f"[build_class_landers] {msg}")


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def format_dt_local(dt: Optional[datetime]) -> str:
    if not dt:
        return "Date/time to be arranged"
    try:
        if ZoneInfo is not None:
            local = dt.astimezone(ZoneInfo("America/New_York"))
        else:
            local = dt.astimezone(timezone.utc)
        return local.strftime("%A, %B %d, %Y at %I:%M %p").lstrip("0").replace(" 0", " ")
    except Exception:
        return dt.isoformat()


def classify_session_time(
    session: Dict[str, Any],
    now: datetime,
) -> str:
    """
    Returns one of: "future", "past", "unknown"
    """
    start = parse_iso(session.get("start_iso") or session.get("start"))
    if not start:
        return "unknown"
    if start >= now:
        return "future"
    return "past"


def build_more_times_label(
    this_session: Dict[str, Any],
    siblings: List[Dict[str, Any]],
    now: datetime,
) -> str:
    time_status = classify_session_time(this_session, now)

    if time_status == "unknown":
        return "See other times and options"

    has_future_sibling = False
    for sib in siblings:
        if sib is this_session:
            continue
        if classify_session_time(sib, now) == "future":
            has_future_sibling = True
            break

    if time_status == "future" and has_future_sibling:
        return "More times?"
    if time_status == "future" and not has_future_sibling:
        return "See other times?"
    # time_status == "past"
    return "Registration closed. See other times?"


def pick_course_title(course: Dict[str, Any]) -> str:
    return (
        course.get("short_name")
        or course.get("name")
        or "CPR / First Aid Course"
    )


def pick_course_tagline(course: Dict[str, Any]) -> str:
    desc = course.get("short_description") or course.get("description")
    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    name = pick_course_title(course)
    return (
        f"{name} with 910 CPR in Wilmington, Burgaw, Jacksonville and "
        f"across Southeastern North Carolina."
    )


def get_session_location(session: Dict[str, Any]) -> str:
    return (
        session.get("location")
        or session.get("location_name")
        or "Exact class address provided in your confirmation email."
    )


def get_register_url(sess: Dict[str, Any], course: Dict[str, Any]) -> str:
    return (
        sess.get("enroll_url")
        or course.get("enroll_url")
        or "https://coastalcprtraining.enrollware.com/schedule"
    )


def get_course_schedule_url(sess: Dict[str, Any], course: Dict[str, Any]) -> str:
    return (
        sess.get("schedule_url")
        or course.get("schedule_url")
        or "https://coastalcprtraining.enrollware.com/schedule"
    )


def pick_hero_image(course: Dict[str, Any]) -> str:
    hero = course.get("hero_image")
    if isinstance(hero, str) and hero.strip():
        return hero.strip()

    cid = course.get("id") or course.get("course_id")
    if cid is not None:
        return f"/images/course-{cid}.jpg"

    return "/images/910cpr-default-class.jpg"


def render_future_sessions_list(
    this_session: Dict[str, Any],
    siblings: List[Dict[str, Any]],
    now: datetime,
) -> str:
    future_sessions: List[Dict[str, Any]] = []
    for sess in siblings:
        if sess is this_session:
            continue
        if classify_session_time(sess, now) == "future":
            future_sessions.append(sess)

    if not future_sessions:
        return "<p>No additional dates are currently scheduled for this class. Please check back soon.</p>"

    future_sessions.sort(
        key=lambda s: parse_iso(s.get("start_iso") or s.get("start")) or now
    )
    future_sessions = future_sessions[:5]

    items: List[str] = []
    for sess in future_sessions:
        start = parse_iso(sess.get("start_iso") or sess.get("start"))
        date_str = escape(format_dt_local(start))
        loc_str = escape(get_session_location(sess))
        reg_url = escape(get_register_url(sess, {}))

        items.append(
            f"""
            <li class="periscope-item">
                <div class="periscope-main">
                    <div class="periscope-date">{date_str}</div>
                    <div class="periscope-location">{loc_str}</div>
                </div>
                <div class="periscope-cta">
                    <a href="{reg_url}" class="btn-secondary">Register</a>
                </div>
            </li>
            """
        )

    return '<ul class="periscope-list">' + "\n".join(items) + "</ul>"


def render_other_classes_block(
    this_course_id: Any,
    courses_by_id: Dict[Any, Dict[str, Any]],
    sessions_by_course: Dict[Any, List[Dict[str, Any]]],
    now: datetime,
) -> str:
    other_courses: List[Dict[str, Any]] = []
    for cid, course in courses_by_id.items():
        if cid == this_course_id:
            continue
        other_courses.append(course)

    if not other_courses:
        return "<p>Explore our full CPR schedule for more options.</p>"

    other_courses = other_courses[:4]

    cards: List[str] = []
    for course in other_courses:
        cid = course.get("id") or course.get("course_id")
        title = escape(pick_course_title(course))
        tagline = escape(pick_course_tagline(course))

        # Try to find the earliest FUTURE session for this course
        link_href = "../schedule.html"
        link_label = "See schedule"

        if cid is not None:
            sessions = sessions_by_course.get(cid, [])
            future_sessions = [
                s for s in sessions if classify_session_time(s, now) == "future"
            ]
            if future_sessions:
                future_sessions.sort(
                    key=lambda s: parse_iso(s.get("start_iso") or s.get("start")) or now
                )
                first_future = future_sessions[0]
                sid = first_future.get("id") or first_future.get("session_id") or first_future.get("enrollware_id")
                if sid is not None:
                    link_href = f"./session-{sid}.html"
                    link_label = "See upcoming dates"

        cards.append(
            f"""
            <article class="other-class-card">
                <h3>{title}</h3>
                <p>{tagline}</p>
                <a href="{link_href}" class="btn-ghost">{link_label}</a>
            </article>
            """
        )

    return '<div class="other-classes-grid">' + "\n".join(cards) + "</div>"


def render_page_html(
    session: Dict[str, Any],
    course: Dict[str, Any],
    siblings: List[Dict[str, Any]],
    courses_by_id: Dict[Any, Dict[str, Any]],
    sessions_by_course: Dict[Any, List[Dict[str, Any]]],
    now: datetime,
) -> str:
    course_title = pick_course_title(course)
    tagline = pick_course_tagline(course)
    hero_image = pick_hero_image(course)

    raw_start_iso = session.get("start_iso") or session.get("start") or ""
    start_dt = parse_iso(raw_start_iso)
    date_str = format_dt_local(start_dt)
    location_str = get_session_location(session)
    price = session.get("price")
    price_str = f"${price:.2f}" if isinstance(price, (int, float)) else ""

    # Status based on GENERATION time (for initial display)
    time_status = classify_session_time(session, now)

    enroll_url = get_register_url(session, course)
    course_schedule_url = get_course_schedule_url(session, course)

    # INITIAL MAIN CTA (will be overridden at runtime by JS if date passes)
    if time_status == "future":
        main_cta_label = "Register for this class"
        main_cta_href = enroll_url
        show_past_banner = False
    elif time_status == "past":
        main_cta_label = "See other times for this class"
        main_cta_href = course_schedule_url
        show_past_banner = True
    else:  # "unknown"
        main_cta_label = "See class options and schedule"
        main_cta_href = course_schedule_url
        show_past_banner = False

    future_block = render_future_sessions_list(session, siblings, now)
    other_block = render_other_classes_block(
        course.get("id") or course.get("course_id"),
        courses_by_id,
        sessions_by_course,
        now,
    )
    more_label = build_more_times_label(session, siblings, now)

    esc_course_title = escape(course_title)
    esc_tagline = escape(tagline)
    esc_date_str = escape(date_str)
    esc_location = escape(location_str)
    esc_price = escape(price_str)
    esc_enroll_url = escape(main_cta_href)
    esc_hero_image = escape(hero_image)
    esc_more_label = escape(more_label)

    past_banner_display = "flex" if show_past_banner else "none"

    past_banner_html = f"""
        <div id="past-banner" class="past-banner" style="display: {past_banner_display};">
            <strong>This class date has already passed.</strong>
            <span>You can still see other upcoming sessions of this class below.</span>
        </div>
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>{esc_course_title} | 910 CPR Class Session</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="{esc_tagline}" />
    <link rel="icon" type="image/png" href="/images/910cpr-favicon.png" />
    <style>
        body {{
            margin: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 40%);
            color: #111827;
        }}
        a {{
            color: #0f766e;
        }}
        .site-header {{
            background: #0f172a;
            color: #f9fafb;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .site-header a {{
            color: #e5e7eb;
            text-decoration: none;
        }}
        .site-header a:hover {{
            text-decoration: underline;
        }}
        .logo {{
            font-weight: 700;
            letter-spacing: .04em;
            text-transform: uppercase;
            font-size: 14px;
        }}
        .nav-links {{
            display: flex;
            gap: 16px;
            font-size: 14px;
        }}
        .page {{
            max-width: 1040px;
            margin: 24px auto 40px auto;
            padding: 0 16px 40px 16px;
        }}
        .hero {{
            display: grid;
            grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
            gap: 20px;
            align-items: center;
            padding: 20px;
            border-radius: 20px;
            background: #ffffff;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.10);
        }}
        .hero-text h1 {{
            margin: 0 0 6px 0;
            font-size: 26px;
        }}
        .hero-text p {{
            margin: 4px 0;
            color: #4b5563;
        }}
        .hero-meta {{
            margin-top: 10px;
            display: grid;
            gap: 4px;
            font-size: 14px;
        }}
        .hero-meta strong {{
            font-weight: 600;
        }}
        .hero-image-wrap {{
            border-radius: 18px;
            overflow: hidden;
            background: #e5f2ff;
            min-height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .hero-image-wrap img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .btn-primary {{
            display: inline-block;
            padding: 10px 18px;
            border-radius: 999px;
            background: #0f766e;
            color: #f9fafb;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            margin-top: 12px;
        }}
        .btn-primary:hover {{
            background: #115e56;
        }}
        .btn-secondary {{
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            border: 1px solid #0f766e;
            color: #0f766e;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
        }}
        .btn-secondary:hover {{
            background: #ecfdf5;
        }}
        .btn-ghost {{
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid #d1d5db;
            color: #111827;
            font-size: 13px;
            text-decoration: none;
        }}
        .btn-ghost:hover {{
            background: #f3f4f6;
        }}
        .past-banner {{
            margin-top: 18px;
            padding: 10px 12px;
            border-radius: 12px;
            background: #fef2f2;
            color: #991b1b;
            border: 1px solid #fecaca;
            font-size: 14px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        .layout {{
            margin-top: 24px;
            display: grid;
            grid-template-columns: minmax(0, 2.2fr) minmax(0, 1.8fr);
            gap: 24px;
        }}
        .card {{
            background: #ffffff;
            border-radius: 16px;
            padding: 16px 18px;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06);
        }}
        .card h2 {{
            margin-top: 0;
            font-size: 18px;
            margin-bottom: 8px;
        }}
        .card p {{
            font-size: 14px;
            color: #4b5563;
        }}
        .periscope-list {{
            list-style: none;
            padding: 0;
            margin: 8px 0 0 0;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .periscope-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 12px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
        }}
        .periscope-date {{
            font-size: 14px;
            font-weight: 600;
        }}
        .periscope-location {{
            font-size: 13px;
            color: #6b7280;
        }}
        .periscope-cta {{
            flex-shrink: 0;
        }}
        .other-classes-grid {{
            display: grid;
            grid-template-columns: minmax(0, 1fr);
            gap: 10px;
            margin-top: 8px;
        }}
        .other-class-card h3 {{
            margin: 0 0 4px 0;
            font-size: 15px;
        }}
        .other-class-card p {{
            margin: 0 0 8px 0;
            font-size: 13px;
            color: #4b5563;
        }}
        .footer-links {{
            margin-top: 26px;
            font-size: 13px;
            color: #6b7280;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .footer-links a {{
            color: #0f766e;
            text-decoration: none;
        }}
        .footer-links a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 800px) {{
            .hero {{
                grid-template-columns: minmax(0, 1fr);
            }}
            .layout {{
                grid-template-columns: minmax(0, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <div class="logo">
            910 CPR · Coastal CPR Training
        </div>
        <nav class="nav-links">
            <a href="https://910cpr.com/">910CPR.com Home</a>
            <a href="../schedule.html">Full CPR Schedule</a>
            <a href="https://coastalcprtraining.enrollware.com/schedule">Enrollware Schedule</a>
        </nav>
    </header>

    <main class="page">
        <section class="hero">
            <div class="hero-text">
                <h1>{esc_course_title}</h1>
                <p>{esc_tagline}</p>

                <div class="hero-meta">
                    <div><strong>Date &amp; time:</strong> {esc_date_str}</div>
                    <div><strong>Location:</strong> {esc_location}</div>
                    {"<div><strong>Price:</strong> " + esc_price + "</div>" if esc_price else ""}
                </div>

                <a
                    id="main-cta"
                    href="{esc_enroll_url}"
                    class="btn-primary"
                    data-start-iso="{escape(raw_start_iso)}"
                    data-enroll-url="{escape(enroll_url)}"
                    data-schedule-url="{escape(course_schedule_url)}"
                    data-status-initial="{time_status}"
                >{escape(main_cta_label)}</a>

                {past_banner_html}
            </div>
            <div class="hero-image-wrap">
                <img src="{esc_hero_image}" alt="{esc_course_title} CPR class in Southeastern North Carolina" />
            </div>
        </section>

        <section class="layout">
            <article class="card">
                <h2>What to expect in this session</h2>
                <p>
                    This is a scheduled session of our <strong>{esc_course_title}</strong> program with 910 CPR.
                    You&apos;ll receive hands-on training, real-world scenarios, and clear guidance on what you
                    need for your job or school requirements.
                </p>
                <p>
                    Full details, pre-course requirements, and confirmation instructions are provided on the
                    registration page and in your confirmation email after you sign up.
                </p>
                <p>
                    If you needed a different time or location, you can use the schedule links on this page to see
                    other upcoming options.
                </p>
            </article>

            <aside class="card">
                <h2 id="more-times-heading">{esc_more_label}</h2>
                {future_block}
            </aside>
        </section>

        <section class="layout" style="margin-top: 18px;">
            <article class="card">
                <h2>Other popular classes at 910 CPR</h2>
                {other_block}
            </article>

            <aside class="card">
                <h2>Need to start over?</h2>
                <p>
                    Not sure this is the right class, or registering someone else? You can jump back to our
                    main course menu or full schedule and re-select the best option for your needs.
                </p>
                <p>
                    For help matching the right class to your hospital, school, or workplace policy,
                    you can always call us at <a href="tel:+19103955193">(910) 395-5193</a>.
                </p>
                <p>
                    <a href="https://910cpr.com/" class="btn-secondary">Return to 910CPR.com</a>
                </p>
                <p>
                    <a href="../schedule.html" class="btn-ghost">See full CPR class schedule</a>
                </p>
            </aside>
        </section>

        <section class="footer-links">
            <span>Still unsure?</span>
            <a href="https://coastalcprtraining.enrollware.com/schedule">View all dates on our Enrollware schedule</a>
            <a href="mailto:brian@910cpr.com">Email 910 CPR</a>
        </section>
    </main>

    <script>
    (function () {{
        var cta = document.getElementById("main-cta");
        if (!cta) return;

        var startIso = cta.dataset.startIso || "";
        var enrollUrl = cta.dataset.enrollUrl || "";
        var scheduleUrl = cta.dataset.scheduleUrl || "";
        var initialStatus = cta.dataset.statusInitial || "unknown";

        var banner = document.getElementById("past-banner");
        var heading = document.getElementById("more-times-heading");

        function applyState(status) {{
            if (status === "future") {{
                cta.textContent = "Register for this class";
                cta.href = enrollUrl || scheduleUrl || cta.href;
                if (banner) banner.style.display = "none";
                if (heading) heading.textContent = "More times?";
            }} else if (status === "past") {{
                cta.textContent = "See other times for this class";
                cta.href = scheduleUrl || enrollUrl || cta.href;
                if (banner) banner.style.display = "flex";
                if (heading) heading.textContent = "Registration closed. See other times?";
            }} else {{
                cta.textContent = "See class options and schedule";
                cta.href = scheduleUrl || enrollUrl || cta.href;
                if (banner) banner.style.display = "none";
                if (heading) heading.textContent = "See other times and options";
            }}
        }}

        var status = initialStatus;

        if (startIso) {{
            var start = new Date(startIso);
            if (!isNaN(start.getTime())) {{
                var now = new Date();
                status = (start > now) ? "future" : "past";
            }} else {{
                status = "unknown";
            }}
        }} else {{
            status = "unknown";
        }}

        applyState(status);
    }})();
    </script>
</body>
</html>
"""
    return html


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    log(f"Repo root is {repo_root}")

    schedule_path = repo_root / "docs" / "data" / "schedule.json"
    out_dir = repo_root / "docs" / "classes"
    out_dir.mkdir(parents=True, exist_ok=True)

    log(f"Loading schedule.json from {schedule_path}")
    with schedule_path.open("r", encoding="utf-8") as f:
        schedule = json.load(f)

    courses: List[Dict[str, Any]] = schedule.get("courses", [])
    sessions: List[Dict[str, Any]] = schedule.get("sessions", [])

    log(f"Loaded {len(courses)} courses and {len(sessions)} sessions")

    courses_by_id: Dict[Any, Dict[str, Any]] = {}
    for course in courses:
        cid = course.get("id") or course.get("course_id")
        if cid is not None:
            courses_by_id[cid] = course

    sessions_by_course: Dict[Any, List[Dict[str, Any]]] = {}
    for sess in sessions:
        cid = sess.get("course_id") or sess.get("courseId") or sess.get("course")
        if cid is None:
            continue
        sessions_by_course.setdefault(cid, []).append(sess)

    now = datetime.now(timezone.utc)

    count = 0
    for sess in sessions:
        cid = sess.get("course_id") or sess.get("courseId") or sess.get("course")
        if cid is None:
            continue

        course = courses_by_id.get(cid)
        if not course:
            continue

        siblings = sessions_by_course.get(cid, [])
        html = render_page_html(
            sess,
            course,
            siblings,
            courses_by_id,
            sessions_by_course,
            now,
        )

        sid = sess.get("id") or sess.get("session_id") or sess.get("enrollware_id")
        if sid is None:
            continue

        out_path = out_dir / f"session-{sid}.html"
        out_path.write_text(html, encoding="utf-8")
        count += 1

    log(f"Built {count} class lander pages in {out_dir}")


if __name__ == "__main__":
    main()
