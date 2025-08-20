import yaml, time
from bots.linkedin_bot import LinkedInBot
from bots.kariyernet_bot import KariyerNetBot

def load_cfg():
    with open("config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    cfg = load_cfg()

    try:
        li = LinkedInBot(cfg)
        li.login()
        li.search_and_apply()
        li.save_log()
        li.close()
        print("[OK] LinkedIn tamamlandı.")
    except Exception as e:
        print("[ERROR] LinkedIn hata:", e)

    time.sleep(2)
    
    # --- LinkedIn bitti ---

    # (İLK ÖNCE) Kariyer.net botunu başlat ve SAYFAYI AÇ
    kn = KariyerNetBot(cfg)
    kn.login()  # -> kariyer.net penceresini açar

    # (SONRA) kullanıcıyı beklet
    input("Kariyer.net penceresi açık. Girişini tamamladıysan Enter'a bas...")

    # ardından devam et
    kn.search_and_apply()
    kn.save_log()
    kn.close()
    print("[OK] Kariyer.net tamamlandı.")
