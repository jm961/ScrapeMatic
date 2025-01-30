from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import os
import threading


app = Flask(__name__)

@dataclass
class Business:
    """Holds business data"""
    name: str = None
    address: str = None
    phone_number: str = None

@dataclass
class BusinessList:
    """Holds list of Business objects and saves to both Excel and CSV"""
    business_list: list[Business] = field(default_factory=list)
    save_at: str = 'output'

    def dataframe(self) -> pd.DataFrame:
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename: str):
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"{self.save_at}/{filename}.xlsx", index=False)

    def save_to_csv(self, filename: str):
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"{self.save_at}/{filename}.csv", index=False)

scrape_thread = None
current_progress = 0  

@app.route('/progress')
def get_progress():
    """Return current scrape progress as JSON."""
    return {'progress': current_progress}

@app.route('/start_scrape', methods=['POST'])
def start_scrape():
    """Starts scraping in a separate thread."""
    global scrape_thread, current_progress
    current_progress = 0  
    data = request.json
    search_term = data["search_term"]
    total = 120  

    def do_scrape():
        global current_progress
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Initial setup - 10% progress
            current_progress = 10
            page.goto("https://www.google.com/maps/@33.8836641,35.5637236,14z?hl=en&entry=ttu", timeout=60000)
            page.wait_for_timeout(5000)

            # Search phase - 20% progress
            current_progress = 20
            page.locator('//input[@id="searchboxinput"]').fill(search_term)
            page.wait_for_timeout(3000)
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
            
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            # Scrolling phase - 20% to 40% progress
            previously_counted = 0
            while True:
                page.mouse.wheel(0, 10000)
                page.wait_for_timeout(2000)

                current_count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                current_progress = 20 + min(20, int((current_count / total) * 20))  # Progress from 20% to 40%
                
                if current_count >= total:
                    listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
                    print(f"Total Scraped: {len(listings)}")
                    break
                elif current_count == previously_counted:
                    listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                    print(f"Arrived at all available\nTotal Scraped: {len(listings)}")
                    break
                else:
                    previously_counted = current_count
                    print(f"Currently Scraped: {current_count}")

            # Data extraction phase - 40% to 100% progress
            business_list = BusinessList()
            total_listings = len(listings) if listings else 1
            
            for idx, anchor in enumerate(listings):
                try:
                    anchor.click()
                    page.wait_for_timeout(800)

                    business = Business(
                        name=anchor.get_attribute('aria-label') or "",
                        address=page.locator('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]').inner_text() if page.locator('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]').count() > 0 else "",
                        phone_number=page.locator('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]').inner_text() if page.locator('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]').count() > 0 else "",
                    )

                    business_list.business_list.append(business)
                    # Update progress from 40% to 100%
                    current_progress = 40 + int(((idx + 1) / total_listings) * 60)
                except Exception as e:
                    print(f'Error occurred: {e}')

            filename = f"google_maps_data_{search_term}".replace(' ', '_')
            business_list.save_to_excel(filename)
            business_list.save_to_csv(filename)

            browser.close()

    scrape_thread = threading.Thread(target=do_scrape)
    scrape_thread.start()
    return {'status': 'scraping started'}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pass
    return render_template('index.html')

@app.route('/results/<search_term>')
def results(search_term):
    filename = f"google_maps_data_{search_term.replace(' ', '_')}"
    return render_template('results.html', search_term=search_term, filename=filename)

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory('output', filename, as_attachment=True)

if __name__ == "__main__":
    import os
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))  
    app.run(debug=False, host=host, port=port)
