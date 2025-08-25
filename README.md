# Instagram Follower/Following Analyzer

This project allows you to extract, compare, and analyze followers and following lists of one or more Instagram profiles using Selenium.

**WARNING:** See the notes section. Since scraping is not allowed by Instagram's policy, this method circumvents the restriction but is not 100% efficient. It can be slow and captures about 95% of the actual followers or following.

## Features
- Automatic login to Instagram
- Extraction of followers and following lists for each user
- Automatic analysis: who doesn't follow you back, who you don't follow back, mutual follows
- Generation of a single report for each user (`analysis_<username>.txt`)

## Requirements
- Python 3.8 or higher
- Google Chrome installed
- ChromeDriver compatible with your Chrome version

## Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/NECKER55/bot_instagram_scraper.git
   cd bot_instagram_scraper
   ```
2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Google Chrome**
   - Download from the official site: https://www.google.com/chrome/
4. **Install ChromeDriver**
   - Find your installed Chrome version:
     ```bash
     google-chrome --version
     ```
   - Download the matching ChromeDriver from: https://sites.google.com/chromium.org/driver/
   - Extract the executable and make sure it's in your PATH or in the same folder as the script.

## Usage
1. Run the script:
   ```bash
   python script.py
   ```
2. Enter your Instagram credentials when prompted (they will be saved in `credentials.txt` for future use).
3. Enter one or more Instagram usernames separated by commas.
4. Wait for scraping and analysis to finish.
5. You will find the reports in files named `analysis_<username>.txt`.

## Notes
- **Never share your `credentials.txt` file**.
- Output and temporary files are excluded from the repository via `.gitignore`.
- Accept or decline cookies to continue the operation when logging in.
- The login may not succeed on the first try; simply rerun the program if needed.
- If Instagram changes its layout or blocks automation, the script may need updates.
- WARNING: The script works as if you were scraping manually, so Instagram may limit the process. If your profile has many followers or following, it will only capture about 95% of them. The final list may be incomplete, but it is a good approximation. You can check the returned users to really see who follows you and who doesn't.

## Example .gitignore
```
*_followers.txt
*_following.txt
analysis_*.txt
downloads/
*.csv
*.log
credentials.txt
*.zip
*.deb
chromedriver-linux64/
__pycache__/
*.pyc
```

## License
This project is for educational and personal use only. Use it responsibly.
