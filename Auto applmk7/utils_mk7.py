import csv,time,random
from selenium.webdriver.common.by import By
def log(m): print(time.strftime("[%H:%M:%S]"),m,flush=True)
def human_pause(a=0.8,b=1.8): time.sleep(random.uniform(a,b))
def cleanup_overlays(driver):
    sels=["button[aria-label*='Kapat']","button[aria-label*='Close']",".artdeco-modal__dismiss"]
    for s in sels:
        for e in driver.find_elements(By.CSS_SELECTOR,s):
            if e.is_displayed(): driver.execute_script("arguments[0].click();",e)
def uniq_by(items,key): 
    seen=set()
    out=[]
    for it in items:
        k=key(it)
        if k not in seen: 
            seen.add(k)
            out.append(it)
    return out
def to_csv(rows,path):
    if not rows:return
    cols=["job_title","company","location","link","match_score"]
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({c:r.get(c,"") for c in cols})
