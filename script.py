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

def human_delay(min_seconds=0.5, max_seconds=2.0):
    """Genera un delay casuale per simulare comportamento umano"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def human_typing(element, text):
    """Simula la digitazione umana con velocità variabile"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.3))  # Velocità di digitazione variabile

def random_mouse_movement(bot):
    """Simula movimenti casuali del mouse"""
    try:
        actions = ActionChains(bot)
        # Movimento casuale del mouse
        x_offset = random.randint(-100, 100)
        y_offset = random.randint(-100, 100)
        actions.move_by_offset(x_offset, y_offset).perform()
        human_delay(0.1, 0.3)
        # Torna indietro
        actions.move_by_offset(-x_offset, -y_offset).perform()
    except:
        pass

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
    human_delay(2, 4)  # Delay più variabile
    
    logging.info("Logging in...")
    username_input = WebDriverWait(bot, random.randint(8, 12)).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
    password_input = WebDriverWait(bot, random.randint(8, 12)).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
    
    # Click sul campo username con delay casuale
    username_input.click()
    human_delay(0.5, 1.5)
    username_input.clear()
    human_delay(0.3, 0.8)
    human_typing(username_input, username)
    
    # Movimento casuale del mouse tra i campi
    random_mouse_movement(bot)
    human_delay(0.5, 1.5)
    
    # Click sul campo password
    password_input.click()
    human_delay(0.5, 1.5)
    password_input.clear()
    human_delay(0.3, 0.8)
    human_typing(password_input, password)
    
    human_delay(0.5, 1.5)
    password_input.send_keys(Keys.RETURN)
    
    human_delay(5, 8)  # Attesa più lunga e variabile dopo login

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
    
    # Delay casuale prima di cercare il link
    human_delay(1, 2.5)
    
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
            wait_time = random.randint(2, 5)
            if selector.startswith("//"):
                element = WebDriverWait(bot, wait_time).until(EC.element_to_be_clickable((By.XPATH, selector)))
            else:
                element = WebDriverWait(bot, wait_time).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            
            # Movimento casuale prima del click
            random_mouse_movement(bot)
            human_delay(0.5, 1.5)
            
            try:
                element.click()
                logging.info(f"Successfully clicked {list_type} link")
                human_delay(1, 2)  # Delay dopo il click
                return True
            except:
                bot.execute_script("arguments[0].click();", element)
                logging.info(f"Successfully clicked {list_type} link using JavaScript")
                human_delay(1, 2)
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
    
    human_delay(3, 5)  # Attesa più variabile dopo apertura dialog
    
    try:
        dialog = WebDriverWait(bot, random.randint(4, 7)).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
        )
        logging.info(f"{list_type.capitalize()} dialog opened successfully")
    except TimeoutException:
        try:
            dialog = bot.find_element(By.CSS_SELECTOR, "div[role='dialog']")
            logging.info(f"{list_type.capitalize()} dialog found via fallback")
        except Exception:
            logging.error(f"{list_type.capitalize()} dialog could not be found at all")
            return

    users = set()
    last_count = 0
    no_change_count = 0
    max_no_change_attempts = 10
    
    scroll_origin = ScrollOrigin.from_element(dialog)
    
    logging.info(f"Expected to collect approximately {expected_count} {list_type}")
    
    # Variabili per comportamento più umano
    scroll_patterns = [200, 300, 400, 500, 250, 350]  # Diversi valori di scroll
    pause_counter = 0
    
    while True:
        try:
            profile_links = bot.find_elements(By.CSS_SELECTOR, "div[role='dialog'] a[href*='/']")
            for link in profile_links:
                href = link.get_attribute('href')
                if href and '/p/' not in href and '/explore/' not in href and '/reels/' not in href:
                    username_extracted = href.strip('/').split('/')[-1]
                    if username_extracted and username_extracted.lower() not in ['', 'instagram', 'accounts']:
                        if '?' not in username_extracted:
                            users.add(username_extracted)
        except Exception as e:
            logging.warning(f"Error collecting profiles: {e}")

        current_count = len(users)
        
        # Log del progresso
        if current_count > last_count:
            logging.info(f"Collected {current_count}/{expected_count} {list_type} so far...")
            last_count = current_count
            no_change_count = 0
        else:
            no_change_count += 1
            logging.debug(f"No new users found. Attempt {no_change_count}/{max_no_change_attempts}")
        
        # Condizioni di uscita
        if current_count >= expected_count:
            logging.info(f"✓ Collected all {expected_count} {list_type}")
            break
        
        if no_change_count >= max_no_change_attempts:
            logging.warning(f"⚠️ No new {list_type} found after {max_no_change_attempts} attempts.")
            logging.info(f"Stopping at {current_count} {list_type} (expected {expected_count})")
            if current_count < expected_count * 0.8:
                logging.warning(f"⚠️ Collected only {current_count}/{expected_count} ({current_count/expected_count*100:.1f}%)")
                logging.warning("Possible reasons: private account, blocked users, or incorrect expected count")
            break
        
        # Pausa casuale ogni tanto (simula lettura/distrazione)
        pause_counter += 1
        if pause_counter % random.randint(5, 10) == 0:
            logging.debug("Taking a longer pause...")
            human_delay(3, 7)
            # Movimento casuale durante la pausa
            random_mouse_movement(bot)
        
        # Scroll con pattern variabile
        scroll_amount = random.choice(scroll_patterns)
        try:
            actions = ActionChains(bot)
            actions.scroll_from_origin(scroll_origin, 0, scroll_amount).perform()
        except Exception:
            try:
                bot.execute_script(f"arguments[0].scrollTop += {scroll_amount};", dialog)
            except:
                logging.warning("Could not perform scroll")
        
        # Pausa variabile dopo scroll
        human_delay(0.8, 2.5)
        
        # Occasionalmente fai uno scroll più piccolo indietro (comportamento umano)
        if random.random() < 0.1:  # 10% di probabilità
            try:
                bot.execute_script(f"arguments[0].scrollTop -= {random.randint(50, 150)};", dialog)
                human_delay(0.5, 1.5)
            except:
                pass
        
        # Controllo di sicurezza per evitare loop infiniti
        if no_change_count > 5:
            try:
                bot.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", dialog)
                human_delay(2, 4)  # Pausa più lunga dopo scroll grande
            except:
                pass
    
    users_list = list(users)
    logging.info(f"✓ Saving {len(users_list)} {list_type} for {username}...")
    with open(f'{username}_{list_type}.txt', 'w') as file:
        file.write('\n'.join(users_list))
    logging.info(f"✓ Successfully saved {len(users_list)} {list_type}")

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
            for username in sorted(followers_not_following):
                file.write(f"   @{username}\n")
            file.write(f"\n\U0001F4E4 FOLLOWING CHE NON TI SEGUONO ({len(following_not_followers)}):\n")
            file.write("-" * 40 + "\n")
            for username in sorted(following_not_followers):
                file.write(f"   @{username}\n")
            file.write(f"\n\U0001F91D FOLLOW RECIPROCI ({len(mutual)}):\n")
            file.write("-" * 40 + "\n")
            for username in sorted(mutual):
                file.write(f"   @{username}\n")
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
    
    # Chiedi il numero di followers e following attesi
    print("\nPer ogni utente, inserisci il numero approssimativo di followers e following.")
    print("Puoi usare formati come: 1000, 1.5K, 2M, etc.\n")
    
    user_counts = {}
    for user in usernames:
        user = user.strip()
        print(f"\nPer @{user}:")
        followers_input = input(f"  Numero di followers (es: 1000, 1.5K): ")
        following_input = input(f"  Numero di following (es: 500, 2K): ")
        
        # Converti gli input in numeri
        followers_count = convert_to_number(followers_input)
        following_count = convert_to_number(following_input)
        
        user_counts[user] = {
            "followers": followers_count,
            "following": following_count
        }
        
        print(f"  ✓ Impostato: {followers_count} followers, {following_count} following")
    
    service = Service('/usr/local/bin/chromedriver')
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent più variabili
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    # Aggiungi viewport size casuale
    viewport_sizes = [(1366, 768), (1920, 1080), (1440, 900), (1536, 864)]
    width, height = random.choice(viewport_sizes)
    options.add_argument(f"--window-size={width},{height}")
    
    bot = webdriver.Chrome(service=service, options=options)
    bot.set_page_load_timeout(30)
    
    try:
        login(bot, username, password)
        
        # Pausa casuale dopo login prima di iniziare lo scraping
        human_delay(3, 6)
        
        for user in usernames:
            user = user.strip()
            try:
                # Usa i conteggi inseriti manualmente
                counts = user_counts[user]
                logging.info(f"\nStarting scrape for {user}:")
                logging.info(f"Expected followers: {counts['followers']}")
                logging.info(f"Expected following: {counts['following']}")
                
                # Pausa casuale tra utenti
                if usernames.index(user) > 0:
                    logging.info("Taking a break between users...")
                    human_delay(10, 20)  # Pausa più lunga tra utenti diversi
                
                # Naviga al profilo
                bot.get(f'https://www.instagram.com/{user}/')
                human_delay(3, 5)
                
                # Movimento casuale sulla pagina del profilo
                random_mouse_movement(bot)
                human_delay(1, 2)
                
                # Scrape followers
                scrape_list(bot, user, counts['followers'], "followers")
                
                # Pausa tra followers e following
                logging.info("Taking a break before scraping following...")
                human_delay(5, 10)
                
                # Torna al profilo prima di aprire following
                bot.get(f'https://www.instagram.com/{user}/')
                human_delay(2, 4)
                
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