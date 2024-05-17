from flask import Flask, request, render_template, redirect, url_for
import requests
from urllib.parse import parse_qs, urlparse, unquote
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def connect_database():
    try:
        # Connect through the local end of the SSH tunnel
        connection = mysql.connector.connect(
            host='0.tcp.ngrok.io',  # Localhost because you're connecting through an SSH tunnel
            user='root',  # Your MySQL username
            password='IcandoIt@2024',  # Your MySQL password
            database='MY_CUSTOM_BOT',  # Your MySQL database name
            port=11341  # Local port that is forwarded to the MySQL server
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None


def save_search_results(url, searchterm, frequency=1):
    conn = connect_database()
    cursor = conn.cursor()
    query = """
    INSERT INTO searchresults (URL, SearchTerm, Frequency)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE Frequency = Frequency + 1;
    """
    cursor.execute(query, (url, searchterm, frequency))
    conn.commit()
    cursor.close()
    conn.close()

def fetch_urls(searchterm):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    search_engines = {
        'google': 'https://www.google.com/search?q=',
        'bing': 'https://www.bing.com/search?q=',
        'yahoo': 'https://search.yahoo.com/search?p=',
        'duckduckgo': 'https://duckduckgo.com/?q='
    }

    for engine, base_url in search_engines.items():
        url = f"{base_url}{searchterm}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        if engine == 'google':
            results = soup.find_all('h3')
        elif engine in ['bing', 'yahoo']:
            results = soup.find_all('h2')
        elif engine == 'duckduckgo':
            results = soup.find_all('a', class_='result__a')

        for result in results:
            link = result.find('a', href=True)
            if not link:
                continue
            href = link['href']
            if engine == 'google' and 'url?q=' in href:
                parsed_url = urlparse(href)
                href = parse_qs(parsed_url.query).get('q', [None])[0]
            elif engine in ['bing', 'yahoo', 'duckduckgo']:
                if href.startswith('/url?'):
                    href = parse_qs(urlparse(href).query).get('q', [None])[0]

            if href:
                href = unquote(href)  # Decodes percent-encoded characters in URL
                save_search_results(href, searchterm)

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