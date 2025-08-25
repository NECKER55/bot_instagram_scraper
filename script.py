import time
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_credentials(username, password):
    with open('credentials.txt', 'w') as file:
        file.write(f"{username}\n{password}")

def load_credentials():
    if not os.path.exists('credentials.txt'):
        return None
    with open('credentials.txt', 'r') as file:
        lines = file.readlines()
        if len(lines) >= 2:
            return lines[0].strip(), lines[1].strip()
    return None

def prompt_credentials():
    username = input("Enter your Instagram username: ")
    password = input("Enter your Instagram password: ")
    save_credentials(username, password)
    return username, password

def login(bot, username, password):
    bot.get('https://www.instagram.com/accounts/login/')
    time.sleep(2)
    
    logging.info("Logging in...")
    username_input = WebDriverWait(bot, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
    password_input = WebDriverWait(bot, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
    
    username_input.clear()
    username_input.send_keys(username)
    password_input.clear()
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)
    
    time.sleep(5)
def get_user_counts(bot, username):
    """Ottiene il numero di follower e following dal profilo, anche per pochi utenti"""
    bot.get(f'https://www.instagram.com/{username}/')
    time.sleep(3)  # Attendere caricamento della pagina
    
    counts = {"followers": 0, "following": 0}
    
    try:
        # Cerca i link che contengono i numeri
        stats_links = bot.find_elements(By.CSS_SELECTOR, "a[href*='/followers/'], a[href*='/following/']")
        
        for link in stats_links:
            href = link.get_attribute('href')
            text = link.text.strip()
            
            # Se il testo è vuoto, prova con l'attributo 'title'
            if not text:
                text = link.get_attribute('title')
            
            list_type = None
            if '/followers' in href:
                list_type = "followers"
            elif '/following' in href:
                list_type = "following"
            
            if list_type and text:
                # Prova a estrarre il numero con regex
                number_match = re.search(r'([\d,\.]+[KMB]?)', text.replace(',', ''))
                if number_match:
                    number_str = number_match.group(1)
                    counts[list_type] = convert_to_number(number_str)
                    logging.info(f"Found {counts[list_type]} {list_type} for {username}")
                else:
                    # fallback: se la regex fallisce ma sappiamo il tipo, assegna almeno 1
                    counts[list_type] = 1
                    logging.info(f"Could not parse number, setting {list_type} = 1 for {username}")
                    
    except Exception as e:
        logging.error(f"Error getting user counts: {e}")
        counts = {"followers": 1, "following": 1}  # fallback per sicurezza
    
    return counts


def convert_to_number(number_str):
    """Converte stringhe come '1.2K' o '1,234' in numeri interi"""
    number_str = number_str.replace(',', '')
    
    if 'K' in number_str.upper():
        return int(float(number_str.replace('K', '').replace('k', '')) * 1000)
    elif 'M' in number_str.upper():
        return int(float(number_str.replace('M', '').replace('m', '')) * 1000000)
    elif 'B' in number_str.upper():
        return int(float(number_str.replace('B', '').replace('b', '')) * 1000000000)
    else:
        return int(float(number_str))

def click_list_link(bot, username, list_type="followers"):
    logging.info(f"Trying to open {list_type} list for {username}...")
    selectors = [
        f"a[href='/{username}/{list_type}/']",
        f"a[href*='/{list_type}/']",
        f"a[href$='/{list_type}/']",
        f"//a[contains(., '{list_type}')]",
        f"//a[contains(., '{list_type.capitalize()}')]",
        f"//span[contains(., '{list_type}')]/parent::a",
        f"//div[contains(., '{list_type}')]/parent::a",
    ]
    for selector in selectors:
        try:
            if selector.startswith("//"):
                element = WebDriverWait(bot, 3).until(EC.element_to_be_clickable((By.XPATH, selector)))
            else:
                element = WebDriverWait(bot, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            try:
                element.click()
                logging.info(f"Successfully clicked {list_type} link")
                return True
            except:
                bot.execute_script("arguments[0].click();", element)
                logging.info(f"Successfully clicked {list_type} link using JavaScript")
                return True
        except TimeoutException:
            continue
    logging.error(f"Could not find or click {list_type} link")
    return False

def scrape_list(bot, username, expected_count, list_type="followers"):
    """Scrape con il numero atteso di utenti"""
    if not click_list_link(bot, username, list_type):
        logging.error(f"Failed to open {list_type} for {username}")
        return
    
    time.sleep(3)
    
    try:
        dialog = WebDriverWait(bot, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
        )
        logging.info(f"{list_type.capitalize()} dialog opened successfully")
        # Prova a cliccare, ma non bloccare in caso di errore
    except TimeoutException:
        # Fallback: cerca comunque il dialog
        try:
            dialog = bot.find_element(By.CSS_SELECTOR, "div[role='dialog']")
            logging.info(f"{list_type.capitalize()} dialog found via fallback")
        except Exception:
            logging.error(f"{list_type.capitalize()} dialog could not be found at all")
            return

    
    users = set()
    last_count = 0
    no_change_count = 0
    
    scroll_origin = ScrollOrigin.from_element(dialog)
    
    logging.info(f"Expected to collect approximately {expected_count} {list_type}")
    
    while True:
        try:
            profile_links = bot.find_elements(By.CSS_SELECTOR, "div[role='dialog'] a[href*='/']")
            for link in profile_links:
                if len(users) >= expected_count:  # stop se raggiunto il numero atteso
                    break

                href = link.get_attribute('href')
                if href and '/p/' not in href and '/explore/' not in href and '/reels/' not in href:
                    username_extracted = href.strip('/').split('/')[-1]

                    if username_extracted and username_extracted.lower() not in [
                        '', 'instagram', 'accounts'
                    ]:
                        if '?' not in username_extracted:  # ignora parametri extra
                            users.add(username_extracted)
        except Exception as e:
            logging.warning(f"Error collecting profiles: {e}")

        current_count = len(users)
        if current_count >= expected_count:
            logging.info(f"Collected all {expected_count} {list_type}")
            break

        # Scroll per caricare altri elementi se non ha raggiunto expected_count
        try:
            actions = ActionChains(bot)
            actions.scroll_from_origin(scroll_origin, 0, 300).perform()
        except Exception:
            bot.execute_script("arguments[0].scrollTop += 300;", dialog)

        time.sleep(random.uniform(0, 1))

    
    users_list = list(users)
    logging.info(f"Saving {len(users_list)} {list_type} for {username}...")
    with open(f'{username}_{list_type}.txt', 'w') as file:
        file.write('\n'.join(users_list))
    logging.info(f"Successfully saved {len(users_list)} {list_type}")


# --- FUNZIONI DI COMPARAZIONE E REPORT ---
def read_usernames_from_file(filename):
    usernames = set()
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                username = line.strip()
                if username:
                    usernames.add(username.lower())
        logging.info(f"Letti {len(usernames)} username da {filename}")
        return usernames
    except FileNotFoundError:
        logging.warning(f"File '{filename}' non trovato!")
        return None
    except Exception as e:
        logging.warning(f"Errore nella lettura del file '{filename}': {e}")
        return None

def save_usernames_to_file(usernames, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            for username in sorted(usernames):
                file.write(f"{username}\n")
        logging.info(f"Salvati {len(usernames)} username in {filename}")
    except Exception as e:
        logging.warning(f"Errore nel salvataggio del file '{filename}': {e}")

def create_detailed_report(base_name, followers, following, followers_not_following, following_not_followers, mutual):
    try:
        with open(f"analysis_{base_name}.txt", 'w', encoding='utf-8') as file:
            file.write("=" * 60 + "\n")
            file.write("INSTAGRAM FOLLOWERS/FOLLOWING ANALYSIS REPORT\n")
            file.write("=" * 60 + "\n\n")
            file.write(f"\U0001F4CA STATISTICHE GENERALI:\n")
            file.write(f"   - Totale Followers: {len(followers)}\n")
            file.write(f"   - Totale Following: {len(following)}\n")
            file.write(f"   - Follow Reciproci: {len(mutual)}\n")
            file.write(f"   - Rapporto Followers/Following: {len(followers)/len(following):.2f}\n" if len(following) > 0 else "N/A\n")
            file.write(f"\n\U0001F4E5 FOLLOWERS CHE NON SEGUI ({len(followers_not_following)}):\n")
            file.write("-" * 40 + "\n")
            for username in sorted(followers_not_following)[:50]:
                file.write(f"   @{username}\n")
            if len(followers_not_following) > 50:
                file.write(f"   ... e altri {len(followers_not_following) - 50}\n")
            file.write(f"\n\U0001F4E4 FOLLOWING CHE NON TI SEGUONO ({len(following_not_followers)}):\n")
            file.write("-" * 40 + "\n")
            for username in sorted(following_not_followers)[:50]:
                file.write(f"   @{username}\n")
            if len(following_not_followers) > 50:
                file.write(f"   ... e altri {len(following_not_followers) - 50}\n")
            file.write(f"\n\U0001F91D FOLLOW RECIPROCI ({len(mutual)}):\n")
            file.write("-" * 40 + "\n")
            for username in sorted(mutual)[:50]:
                file.write(f"   @{username}\n")
            if len(mutual) > 50:
                file.write(f"   ... e altri {len(mutual) - 50}\n")
        logging.info(f"Report dettagliato salvato in analysis_{base_name}.txt")
    except Exception as e:
        logging.warning(f"Errore nella creazione del report: {e}")

def analyze_followers_following(followers_file, following_file):
    logging.info(f"Analisi: {followers_file} vs {following_file}")
    followers = read_usernames_from_file(followers_file)
    following = read_usernames_from_file(following_file)
    if followers is None or following is None:
        logging.warning("Impossibile procedere con l'analisi.")
        return
    followers_not_following = followers - following
    following_not_followers = following - followers
    mutual = followers & following
    base_name = followers_file.replace('_followers.txt', '').replace('.txt', '')
    # Non salvare più i file separati, solo il report unico
    create_detailed_report(base_name, followers, following, followers_not_following, following_not_followers, mutual)
    logging.info(f"Analisi completata per {base_name}")

def scrape():
    credentials = load_credentials()
    if credentials is None:
        username, password = prompt_credentials()
    else:
        username, password = credentials
    
    usernames = input("Enter the Instagram usernames you want to scrape (separated by commas): ").split(",")
    
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    bot = webdriver.Chrome(service=service, options=options)
    bot.set_page_load_timeout(30)
    
    try:
        login(bot, username, password)
        for user in usernames:
            user = user.strip()
            try:
                # Ottieni i conteggi di follower e following
                counts = get_user_counts(bot, user)
                logging.info(f"\nStarting scrape for {user}:")
                logging.info(f"Expected followers: {counts['followers']}")
                logging.info(f"Expected following: {counts['following']}")
                # Scrape followers
                scrape_list(bot, user, counts['followers'], "followers")
                # Scrape following
                scrape_list(bot, user, counts['following'], "following")
                # Analisi automatica dopo scraping
                followers_file = f"{user}_followers.txt"
                following_file = f"{user}_following.txt"
                analyze_followers_following(followers_file, following_file)
            except Exception as e:
                logging.error(f"Error scraping {user}: {e}")
                continue
    finally:
        bot.quit()

if __name__ == '__main__':
    TIMEOUT = 15
    scrape()