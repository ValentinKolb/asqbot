import urllib.request
import urllib.parse
import time
import re
import html
import http.cookiejar
import getpass
import ssl
import sys
import gzip
import random
from urllib.error import HTTPError

def decompress_response(response):
    """Decompresses a gzipped response if necessary."""
    if response.info().get('Content-Encoding') == 'gzip':
        data = response.read()
        return gzip.decompress(data).decode('utf-8')
    else:
        return response.read().decode('utf-8')

def login(username, password, disable_ssl_verification=False):
    """Performs the login process and returns the session cookies."""
    login_url = 'https://campusonline.uni-ulm.de/CoronaNG/index.html'

    # Create cookie jar to store cookies
    cookie_jar = http.cookiejar.CookieJar()

    # Set up opener with SSL context if needed
    if disable_ssl_verification:
        # Create an SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar),
            urllib.request.HTTPSHandler(context=ssl_context)
        )
    else:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    urllib.request.install_opener(opener)

    # First, get the login page to obtain initial cookies
    try:
        initial_req = urllib.request.Request(
            login_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,de;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )

        with opener.open(initial_req) as response:
            # Just read the response to ensure cookies are saved
            decompress_response(response)
            print("Initial page loaded successfully")
    except Exception as e:
        print(f"Error loading initial login page: {e}")

    # Prepare login data
    login_data = {
        'uid': username,
        'password': password
    }
    data_encoded = urllib.parse.urlencode(login_data).encode('ascii')

    # Login headers based on provided information
    login_headers = {
        'Host': 'campusonline.uni-ulm.de',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,de;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://campusonline.uni-ulm.de/CoronaNG/index.html',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://campusonline.uni-ulm.de',
        'DNT': '1',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i'
    }

    # Send login request
    req = urllib.request.Request(login_url, data=data_encoded, headers=login_headers, method='POST')

    try:
        with opener.open(req) as response:
            # Handle potentially compressed response
            try:
                html_content = decompress_response(response)

                # Check if login was successful
                if "Abmelden" in html_content:
                    print("Login successful!")
                else:
                    print("Login failed. Please check your credentials.")
                    return None
            except Exception as e:
                print(f"Error decoding response: {e}")
                # Try binary mode as fallback
                response_data = response.read()
                print(f"Received {len(response_data)} bytes of data")
                return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None

    # Extract JSESSIONID from cookies
    jsessionid = None
    for cookie in cookie_jar:
        if cookie.name == "JSESSIONID":
            jsessionid = cookie.value
            break

    if jsessionid:
        print(f"Login ID obtained: {jsessionid}")
    else:
        print("No login ID received.")

    return cookie_jar

def check_registrations(cookie_jar, asq_ids, disable_ssl_verification=False):
    """Regularly checks registrations with the specified ASQ-IDs."""
    url = 'https://campusonline.uni-ulm.de/CoronaNG/user/mycorona.html'

    # Headers for registration check
    headers = {
        'Host': 'campusonline.uni-ulm.de',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
        'Accept-Language': 'en-US,de;q=0.7,en;q=0.3',
        'Referer': 'https://campusonline.uni-ulm.de/CoronaNG/user/mycorona.html',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://campusonline.uni-ulm.de',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i'
    }

    # Create opener with cookies and SSL context if needed
    if disable_ssl_verification:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar),
            urllib.request.HTTPSHandler(context=ssl_context)
        )
    else:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    # First, get the page without submitting the form
    try:
        initial_req = urllib.request.Request(url, headers=headers)
        with opener.open(initial_req) as response:
            decompress_response(response)
            print("Successfully loaded page")
    except Exception as e:
        print(f"Error loading initial page: {e}")
        return

    # Create data for POST request
    data = {
        'action': '5',
        'scope': 'inspections'
    }

    for i, asq_id in enumerate(asq_ids):
        data[f'check_{asq_id}'] = 'on'
        data[f'sort_{asq_id}'] = '000'

    # Endless loop with 1-second interval (like watch -n 1)
    try:
        while True:
            # Convert to URL-encoded string (regenerate each time to avoid caching issues)
            data_encoded = urllib.parse.urlencode(data)
            data_bytes = data_encoded.encode('ascii')

            # Send HTTP request
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')

            try:
                with opener.open(req) as response:
                    try:
                        html_content = decompress_response(response)

                        # Extract relevant information
                        info_pattern = r'Info: (\d+) Teilnahmen waren erfolgreich\.'
                        error_pattern = r'Error: (\d+) versuchte Teilnahmen fehlgeschlagen\.'

                        info_match = re.search(info_pattern, html_content)
                        error_match = re.search(error_pattern, html_content)

                        # Current time for timestamp
                        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                        print(f"\n[{current_time}] Result:")

                        if info_match:
                            print(f"Info: {info_match.group(1)} registrations were successful.")

                        if error_match:
                            print(f"Error: {error_match.group(1)} attempted registrations failed.")

                            # Extract specific error messages
                            error_messages = re.findall(r'Error: ([^<\n]+)', html_content)
                            for i, msg in enumerate(error_messages):
                                if i < len(error_messages) - 1:  # Skip the last summary
                                    print(f"  - {html.unescape(msg.strip())}")

                        if not info_match and not error_match:
                            print("No information about registrations found.")

                            # If we're getting a response but no patterns match, log a snippet
                            print("Response snippet (first 200 chars):", html_content[:200])
                    except Exception as e:
                        print(f"Error processing response: {e}")

            except urllib.error.HTTPError as e:
                print(f"Error sending request: HTTP Error {e.code}: {e.reason}")
                if e.code == 403:
                    print("403 Forbidden error - session may have expired. Attempting to refresh...")
                    try:
                        # Try to refresh the page
                        refresh_req = urllib.request.Request(url, headers=headers)
                        with opener.open(refresh_req) as response:
                            refresh_html = decompress_response(response)
                            print("Page refreshed successfully")
                    except Exception as refresh_error:
                        print(f"Error refreshing page: {refresh_error}")
            except urllib.error.URLError as e:
                print(f"Error sending request: {e}")

            # Add a small random delay to avoid being detected as a bot
            delay = 1 + random.random() * .1
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")

def main():
    print("CoronaNG Registration Bot")
    print("=========================")

    # Check for command line arguments
    disable_ssl_verification = False
    if len(sys.argv) > 1 and sys.argv[1] == "--no-ssl-verify":
        disable_ssl_verification = True
        print("Warning: SSL certificate verification disabled!")

    # Request login credentials
    username = input(">>> Username (e.g., xyz42): ")
    password = getpass.getpass(">>> Password: ")

    # Perform login
    cookie_jar = login(username, password, disable_ssl_verification)

    if not cookie_jar:
        print("Login failed. Program will exit.")
        return

    # Interactively read ASQ-IDs
    print("\nPlease enter the ASQ-IDs (one per line, empty line to finish)")

    asq_ids = []
    first_input = input(">>> ASQ-ID: ")

    if first_input.strip():
        asq_ids.append(first_input.strip())

    while True:
        asq_id = input(">>> ASQ-ID (empty line to finish): ")
        if not asq_id.strip():
            break
        asq_ids.append(asq_id.strip())

    if not asq_ids:
        print("No ASQ-IDs entered. Exiting program.")
        return

    print(f"\nChecking registrations for {len(asq_ids)} ASQ-IDs: {', '.join(asq_ids)}")
    print("Press Ctrl+C to exit the program.")

    # Check registrations
    check_registrations(cookie_jar, asq_ids, disable_ssl_verification)

if __name__ == "__main__":
    main()
