pip install pytrends requests beautifulsoup4 matplotlib pandas

import requests
import pandas as pd
import matplotlib.pyplot as plt
from pytrends.request import TrendReq
from datetime import datetime
from bs4 import BeautifulSoup

# Initialize Pytrends
pytrends = TrendReq(hl='en-US', tz=360)

def get_trend_data(keywords):
    pytrends.build_payload(keywords, cat=0, timeframe='today 5-y', geo='', gprop='')
    trend_data = pytrends.interest_over_time()
    return trend_data

def get_domain_age(domain):
    url = f"https://www.whois.com/whois/{domain}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    creation_date = None
    for div in soup.find_all("div", {"data-ref": "registrar-data"}):
        if "Creation Date" in div.text:
            creation_date = div.text.split(":")[-1].strip()
            break
    if creation_date:
        creation_date = datetime.strptime(creation_date, '%Y-%m-%dT%H:%M:%S.%fZ')
        age = (datetime.now() - creation_date).days / 365
        return round(age, 2)
    return None

def get_backlinks(api_key, domain):
    # Example using Moz API (replace with actual request logic)
    url = f"https://moz.com/api/v1/links?site={domain}&api_key={api_key}"
    response = requests.get(url)
    data = response.json()
    return {
        'total_external_links': data['total_external_links'],
        'followed_links': data['followed_links'],
        'domain_authority': data['domain_authority'],
        'linking_domains': data['linking_domains'],
    }

def get_site_speed(api_key, domain):
    url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=http://{domain}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    speed_scores = {
        "desktop": data['lighthouseResult']['categories']['performance']['score'] * 100,
        "mobile": data['originLoadingExperience']['metrics']['FIRST_CONTENTFUL_PAINT_MS']['percentile'] if 'originLoadingExperience' in data and 'metrics' in data['originLoadingExperience'] else None
    }
    return speed_scores

def check_mobile_friendly(api_key, domain):
    url = f"https://searchconsole.googleapis.com/v1/urlTestingTools/mobileFriendlyTest:run?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {'url': f"http://{domain}"}
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    return result['mobileFriendliness'] == "MOBILE_FRIENDLY" if 'mobileFriendliness' in result else False

def analyze_content(domain):
    url = f"http://{domain}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content = soup.get_text()
    word_count = len(content.split())
    return {"word_count": word_count, "content": content}

def get_social_media_mentions(api_key, domain):
    # Example using a hypothetical social media API (replace with actual request logic)
    url = f"https://socialmediaapi.com/api/v1/mentions?site={domain}&api_key={api_key}"
    response = requests.get(url)
    data = response.json()
    return data['total_mentions']

def get_traffic_data(api_key, domain):
    # Example using a hypothetical traffic API (replace with actual request logic)
    url = f"https://trafficapi.com/api/v1/traffic?site={domain}&api_key={api_key}"
    response = requests.get(url)
    data = response.json()
    return data['total_visits']

def get_similar_domain_sales(api_key):
    url = "https://api.godaddy.com/v1/marketplace/listings/sold"
    headers = {"Authorization": f"sso-key {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def normalize_score(value, max_value, scale=20):
    return (value / max_value) * scale if max_value else 0

def appraise_domain(domain, api_key):
    keywords = domain.replace(".com", "").split()
    trend_data = get_trend_data(keywords)
    domain_age = get_domain_age(domain)
    backlinks_data = get_backlinks(api_key, domain)
    site_speed = get_site_speed(api_key, domain)
    mobile_friendly = check_mobile_friendly(api_key, domain)
    content_analysis = analyze_content(domain)
    social_mentions = get_social_media_mentions(api_key, domain)
    traffic_data = get_traffic_data(api_key, domain)
    similar_sales = get_similar_domain_sales(api_key)

    # Max values for normalization
    max_values = {
        'total_external_links': 1000,
        'followed_links': 1000,
        'domain_authority': 100,
        'linking_domains': 100,
        'content_word_count': 1000,
        'social_mentions': 1000,
        'traffic_data': 1000
    }

    # Normalize and combine scores
    trend_score = normalize_score(trend_data.mean().mean(), 100) if not trend_data.empty else 0
    domain_age_score = normalize_score(domain_age, 20) if domain_age else 0
    backlink_score = normalize_score(backlinks_data['total_external_links'], max_values['total_external_links'])
    followed_links_score = normalize_score(backlinks_data['followed_links'], max_values['followed_links'])
    domain_authority_score = normalize_score(backlinks_data['domain_authority'], max_values['domain_authority'])
    linking_domains_score = normalize_score(backlinks_data['linking_domains'], max_values['linking_domains'])
    site_speed_score = (site_speed['desktop'] + site_speed['mobile']) / 2 if site_speed['mobile'] else site_speed['desktop']
    mobile_friendly_score = 10 if mobile_friendly else 0
    content_score = normalize_score(content_analysis['word_count'], max_values['content_word_count'])
    social_mentions_score = normalize_score(social_mentions, max_values['social_mentions'])
    traffic_score = normalize_score(traffic_data, max_values['traffic_data'])

    # Example total score calculation
    total_score = (trend_score + domain_age_score + backlink_score + followed_links_score + domain_authority_score +
                   linking_domains_score + site_speed_score + mobile_friendly_score + content_score + social_mentions_score + traffic_score)

    # Estimate value based on similar sales and score
    similar_prices = [sale["price"] for sale in similar_sales['listings'] if sale["price"] is not None]
    estimated_value = sum(similar_prices) / len(similar_prices) * (total_score / 100) if similar_prices else 0

    return {
        "domain": domain,
        "trend_score": trend_score,
        "domain_age": domain_age,
        "backlinks_data": backlinks_data,
        "site_speed": site_speed,
        "mobile_friendly": mobile_friendly,
        "content_analysis": content_analysis,
        "social_mentions": social_mentions,
        "traffic_data": traffic_data,
        "total_score": total_score,
        "estimated_value": estimated_value
    }

# Replace with your actual API key
API_KEY = "AIzaSyCz1irk06W9gW6jcOGVG5o8KEmtf9WmgW0"

# Appraise the domain
domain = "domain"  # Replace with the domain you want to appraise
appraisal = appraise_domain(domain, API_KEY)
print(appraisal)

# Plot the trend data
keywords = domain.replace(".com", "").split()
trend_data = get_trend_data(keywords)
if not trend_data.empty:
    plt.figure(figsize=(14, 7))
    trend_data.plot()
    plt.title(f'Trend Data for {keywords}')
    plt.xlabel('Date')
    plt.ylabel('Interest')
    plt.show()
