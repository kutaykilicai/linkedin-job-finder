from jinja2 import Template
import yaml, datetime

def _pick_summary(profile: dict, max_len: int | None):
    long = (profile.get("summary") or "").strip()
    short = (profile.get("short_summary") or "").strip()
    if not max_len:
        return long or short
    if long and len(long) <= max_len:
        return long
    if short and len(short) <= max_len:
        return short
    src = long or short
    if not src:
        return ""
    ell = "…"
    return (src[: max_len - 1]).rstrip() + ell if max_len and len(src) > max_len else src

def render_cover_letter(template_path: str, profile_yaml: str, company: str, role: str, city: str, max_len: int | None = None):
    profile = yaml.safe_load(open(profile_yaml, "r", encoding="utf-8"))
    summary = _pick_summary(profile, max_len)
    with open(template_path, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())
    txt = tmpl.render(
        today=datetime.date.today().strftime("%d.%m.%Y"),
        name=profile.get("name",""),
        title=profile.get("title",""),
        summary=summary,
        skills=", ".join(profile.get("skills", [])),
        company=company or "",
        role=role or "",
        city=city or "",
    )
    if max_len and len(txt) > max_len:
        txt = txt[: max_len - 1].rstrip() + "…"
    return txt
