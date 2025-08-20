import re
def extract_experience(desc:str):
    if not desc: return "belirtilmemiş","belirsiz"
    m=re.search(r'(\d+)\s*-\s*(\d+)\s*yıl',desc.lower())
    if m: return f"{m[1]}-{m[2]} yıl","deneyim yakın"
    return "belirtilmemiş","belirsiz"

def score_job(job):
    text=(job.get("job_title","")+" "+job.get("description","")).lower()
    score=0; reasons=[]; risks=[]
    if "it audit" in text: score+=20; reasons.append("IT Audit")
    if "iso 27001" in text: score+=15; reasons.append("ISO27001")
    if "cobit" in text: score+=15; reasons.append("COBIT")
    if "nist" in text: score+=12; reasons.append("NIST")
    if "cloud" in text: score+=10; reasons.append("Cloud")
    if "aws" in text: score+=8; reasons.append("AWS")
    if "azure" in text: score+=8; reasons.append("Azure")
    if "wireshark" in text: score+=6; reasons.append("Wireshark")
    if "nessus" in text: score+=6; reasons.append("Nessus")
    if "burp" in text: score+=6; reasons.append("Burp")
    if "helpdesk" in text: score-=10; risks.append("Helpdesk")
    exp_text,interp=extract_experience(text)
    return {"match_score":max(0,min(100,score)),
            "experience_required_text":exp_text,
            "experience_interpretation":interp,
            "top_reasons":reasons,"risks_or_gaps":risks}
