from flask import Flask, request, render_template, redirect, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib.parse import parse_qs, urlparse, unquote
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import time

app = Flask(__name__)

def connect_database():
    try:
        # Connect to the MySQL Database
        connection = mysql.connector.connect(
            host='localhost', 
            user='root', 
            password='IcandoIt@2024', 
            database='MY_CUSTOM_BOT',
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def setup_driver():
    options = Options()
    options.headless = True
    # ChromeDriver added in Environmental System Variable PATH
    driver = webdriver.Chrome(options=options) 
    return driver

def save_search_results(url, searchterm, frequency=1):
    conn = connect_database()
    if not conn:
        print("Database connection failed")
        return
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO searchresults (URL, SearchTerm, Frequency)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE Frequency = Frequency + 1;
        """
        cursor.execute(query, (url, searchterm, frequency))
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Error in database operation: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def fetch_urls(searchterm):
    driver = setup_driver()
    search_engines = {
        'google': 'https://www.google.com/search?q=',
        'bing': 'https://www.bing.com/search?q=',
        'yahoo': 'https://search.yahoo.com/search?p=',
        'duckduckgo': 'https://duckduckgo.com/?q=',
        'dogpile': 'https://www.dogpile.com/search?q='
    }

    try:
        for engine, base_url in search_engines.items():
            urls_collected = []
            page = 0
            while len(urls_collected) < 30 and page < 1: 
                url = f"{base_url}{searchterm}&start={page * 10}"
                driver.get(url)
                time.sleep(3) 

                # Take a screenshot for each engine
                screenshot_path = f"C:/Users/Shradha Godse/Downloads/screenshots/{engine}_{searchterm.replace(' ', '_')}_{page}.png"
                driver.save_screenshot(screenshot_path)
                
                # Wait for the search results to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h3, h2'))
                )

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                # Google and Bing commonly use <h3>, others might use <h2>
                results = soup.find_all(['h3', 'h2'])  

                for result in results:
                    link = result.find('a', href=True)
                    if link:
                        href = link['href']
                         # Common URL patterns
                        if 'url?q=' in href or 'search?p=' in href: 
                            parsed_url = urlparse(href)
                            href = parse_qs(parsed_url.query).get('q', [None])[0]
                            href = unquote(href) if href else None
                        if href and href not in urls_collected:
                            urls_collected.append(href)
                            if len(urls_collected) >= 30:
                                break
                page += 1
            for url in urls_collected:
                save_search_results(url, searchterm)
    finally:
        driver.quit()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        search_term = request.form.get('search', '')
        if search_term:
            fetch_urls(search_term)
            return redirect(url_for('results', search_term=search_term))
    return render_template('index.html')

@app.route('/results.html')
def results():
    search_term = request.args.get('search_term', '')
    conn = connect_database()
    cursor = conn.cursor()
    query = """
    SELECT URL, Frequency FROM searchresults
    WHERE SearchTerm = %s ORDER BY Frequency DESC;
    """
    cursor.execute(query, (search_term,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('results.html', data=data, search_term=search_term)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)
