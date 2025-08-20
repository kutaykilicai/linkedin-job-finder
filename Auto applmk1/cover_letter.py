from jinja2 import Template
import yaml, datetime

def render_cover_letter(template_path: str, profile_yaml: str, company: str, role: str, city: str):
    profile = yaml.safe_load(open(profile_yaml, "r", encoding="utf-8"))
    with open(template_path, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())
    return tmpl.render(
        today=datetime.date.today().strftime("%d.%m.%Y"),
        name=profile["name"],
        title=profile["title"],
        summary=profile["summary"],
        skills=", ".join(profile["skills"]),
        company=company,
        role=role,
        city=city,
    )
