import yaml, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from utils.logging_setup import setup_logger
from bots.linkedin_bot import LinkedInBot
from bots.kariyernet_bot import KariyerNetBot

def load_cfg():
    with open("config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    log = setup_logger()
    cfg = load_cfg()

    # ChromeDriver başlatma
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        li = LinkedInBot(cfg)
        li.login()
        li.search_and_apply()
        li.save_log()
        li.close()
        log.info("LinkedIn tamamlandı.")
    except Exception as e:
        log.error(f"LinkedIn hata: {e}")

    time.sleep(3)

    try:
        kn = KariyerNetBot(cfg)
        kn.login()
        kn.search_and_apply()
        kn.save_log()
        kn.close()
        log.info("Kariyer.net tamamlandı.")
    except Exception as e:
        log.error(f"Kariyer.net hata: {e}")
