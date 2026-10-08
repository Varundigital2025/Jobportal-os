"""
currency_service.py - Country and Currency Mapping Service
Provides country definitions, currency symbols, and location-based auto-detection.
"""

GLOBAL_COUNTRIES_CURRENCIES = [
    {
        'country': 'India',
        'code': 'IN',
        'symbol': '₹',
        'currency_code': 'INR',
        'currency_name': 'Indian Rupee',
        'flag': '🇮🇳',
        'keywords': ['india', 'bharat', 'bengaluru', 'bangalore', 'delhi', 'new delhi', 'mumbai', 'hyderabad', 'chennai', 'pune', 'kolkata', 'noida', 'gurgaon', 'gurugram', 'ahmedabad', 'jaipur', 'kerala', 'indore', 'chandigarh']
    },
    {
        'country': 'United States',
        'code': 'US',
        'symbol': '$',
        'currency_code': 'USD',
        'currency_name': 'US Dollar',
        'flag': '🇺🇸',
        'keywords': ['united states', 'usa', 'us', 'new york', 'san francisco', 'california', 'austin', 'texas', 'seattle', 'washington', 'chicago', 'boston', 'los angeles', 'miami', 'denver', 'atlanta', 'dallas', 'silicon valley']
    },
    {
        'country': 'United Kingdom',
        'code': 'GB',
        'symbol': '£',
        'currency_code': 'GBP',
        'currency_name': 'British Pound',
        'flag': '🇬🇧',
        'keywords': ['united kingdom', 'uk', 'great britain', 'england', 'london', 'manchester', 'birmingham', 'edinburgh', 'glasgow', 'leeds', 'bristol', 'cambridge', 'oxford']
    },
    {
        'country': 'European Union',
        'code': 'EU',
        'symbol': '€',
        'currency_code': 'EUR',
        'currency_name': 'Euro',
        'flag': '🇪🇺',
        'keywords': ['germany', 'france', 'spain', 'italy', 'netherlands', 'ireland', 'belgium', 'portugal', 'austria', 'finland', 'greece', 'berlin', 'munich', 'paris', 'amsterdam', 'dublin', 'madrid', 'barcelona', 'rome', 'milan', 'brussels', 'lisbon', 'vienna']
    },
    {
        'country': 'Canada',
        'code': 'CA',
        'symbol': 'C$',
        'currency_code': 'CAD',
        'currency_name': 'Canadian Dollar',
        'flag': '🇨🇦',
        'keywords': ['canada', 'toronto', 'vancouver', 'montreal', 'ottawa', 'calgary', 'edmonton', 'quebec', 'ontario', 'british columbia']
    },
    {
        'country': 'Australia',
        'code': 'AU',
        'symbol': 'A$',
        'currency_code': 'AUD',
        'currency_name': 'Australian Dollar',
        'flag': '🇦🇺',
        'keywords': ['australia', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'canberra', 'gold coast']
    },
    {
        'country': 'United Arab Emirates',
        'code': 'AE',
        'symbol': 'AED',
        'currency_code': 'AED',
        'currency_name': 'UAE Dirham',
        'flag': '🇦🇪',
        'keywords': ['united arab emirates', 'uae', 'dubai', 'abu dhabi', 'sharjah']
    },
    {
        'country': 'Singapore',
        'code': 'SG',
        'symbol': 'S$',
        'currency_code': 'SGD',
        'currency_name': 'Singapore Dollar',
        'flag': '🇸🇬',
        'keywords': ['singapore']
    },
    {
        'country': 'Japan',
        'code': 'JP',
        'symbol': '¥',
        'currency_code': 'JPY',
        'currency_name': 'Japanese Yen',
        'flag': '🇯🇵',
        'keywords': ['japan', 'tokyo', 'osaka', 'kyoto', 'yokohama', 'nagoya']
    },
    {
        'country': 'Switzerland',
        'code': 'CH',
        'symbol': 'CHF',
        'currency_code': 'CHF',
        'currency_name': 'Swiss Franc',
        'flag': '🇨🇭',
        'keywords': ['switzerland', 'zurich', 'geneva', 'basel', 'bern', 'lausanne']
    },
    {
        'country': 'Saudi Arabia',
        'code': 'SA',
        'symbol': 'SAR',
        'currency_code': 'SAR',
        'currency_name': 'Saudi Riyal',
        'flag': '🇸🇦',
        'keywords': ['saudi arabia', 'ksa', 'riyadh', 'jeddah', 'dammam']
    },
    {
        'country': 'Brazil',
        'code': 'BR',
        'symbol': 'R$',
        'currency_code': 'BRL',
        'currency_name': 'Brazilian Real',
        'flag': '🇧🇷',
        'keywords': ['brazil', 'brasil', 'são paulo', 'sao paulo', 'rio de janeiro', 'curitiba']
    },
    {
        'country': 'South Africa',
        'code': 'ZA',
        'symbol': 'R',
        'currency_code': 'ZAR',
        'currency_name': 'South African Rand',
        'flag': '🇿🇦',
        'keywords': ['south africa', 'johannesburg', 'cape town', 'durban', 'pretoria']
    },
    {
        'country': 'New Zealand',
        'code': 'NZ',
        'symbol': 'NZ$',
        'currency_code': 'NZD',
        'currency_name': 'New Zealand Dollar',
        'flag': '🇳🇿',
        'keywords': ['new zealand', 'auckland', 'wellington', 'christchurch']
    },
    {
        'country': 'Philippines',
        'code': 'PH',
        'symbol': '₱',
        'currency_code': 'PHP',
        'currency_name': 'Philippine Peso',
        'flag': '🇵🇭',
        'keywords': ['philippines', 'manila', 'cebu', 'quezon city', 'davao']
    },
    {
        'country': 'Malaysia',
        'code': 'MY',
        'symbol': 'RM',
        'currency_code': 'MYR',
        'currency_name': 'Malaysian Ringgit',
        'flag': '🇲🇾',
        'keywords': ['malaysia', 'kuala lumpur', 'penang', 'johor bahru']
    },
    {
        'country': 'Indonesia',
        'code': 'ID',
        'symbol': 'Rp',
        'currency_code': 'IDR',
        'currency_name': 'Indonesian Rupiah',
        'flag': '🇮🇩',
        'keywords': ['indonesia', 'jakarta', 'bali', 'surabaya', 'bandung']
    },
    {
        'country': 'Thailand',
        'code': 'TH',
        'symbol': '฿',
        'currency_code': 'THB',
        'currency_name': 'Thai Baht',
        'flag': '🇹🇭',
        'keywords': ['thailand', 'bangkok', 'chiang mai', 'phuket']
    },
    {
        'country': 'Vietnam',
        'code': 'VN',
        'symbol': '₫',
        'currency_code': 'VND',
        'currency_name': 'Vietnamese Dong',
        'flag': '🇻🇳',
        'keywords': ['vietnam', 'ho chi minh', 'hanoi', 'da nang']
    },
    {
        'country': 'Nigeria',
        'code': 'NG',
        'symbol': '₦',
        'currency_code': 'NGN',
        'currency_name': 'Nigerian Naira',
        'flag': '🇳🇬',
        'keywords': ['nigeria', 'lagos', 'abuja', 'ibadan']
    },
    {
        'country': 'Kenya',
        'code': 'KE',
        'symbol': 'KSh',
        'currency_code': 'KES',
        'currency_name': 'Kenyan Shilling',
        'flag': '🇰🇪',
        'keywords': ['kenya', 'nairobi', 'mombasa']
    },
    {
        'country': 'Israel',
        'code': 'IL',
        'symbol': '₪',
        'currency_code': 'ILS',
        'currency_name': 'Israeli New Shekel',
        'flag': '🇮🇱',
        'keywords': ['israel', 'tel aviv', 'jerusalem', 'haifa']
    },
    {
        'country': 'Turkey',
        'code': 'TR',
        'symbol': '₺',
        'currency_code': 'TRY',
        'currency_name': 'Turkish Lira',
        'flag': '🇹🇷',
        'keywords': ['turkey', 'türkiye', 'istanbul', 'ankara', 'izmir']
    },
    {
        'country': 'South Korea',
        'code': 'KR',
        'symbol': '₩',
        'currency_code': 'KRW',
        'currency_name': 'South Korean Won',
        'flag': '🇰🇷',
        'keywords': ['south korea', 'korea', 'seoul', 'busan', 'incheon']
    },
    {
        'country': 'China',
        'code': 'CN',
        'symbol': '¥',
        'currency_code': 'CNY',
        'currency_name': 'Chinese Yuan',
        'flag': '🇨🇳',
        'keywords': ['china', 'beijing', 'shanghai', 'shenzhen', 'guangzhou', 'hangzhou']
    },
    {
        'country': 'Pakistan',
        'code': 'PK',
        'symbol': 'Rs',
        'currency_code': 'PKR',
        'currency_name': 'Pakistani Rupee',
        'flag': '🇵🇰',
        'keywords': ['pakistan', 'karachi', 'lahore', 'islamabad', 'rawalpindi']
    },
    {
        'country': 'Bangladesh',
        'code': 'BD',
        'symbol': '৳',
        'currency_code': 'BDT',
        'currency_name': 'Bangladeshi Taka',
        'flag': '🇧🇩',
        'keywords': ['bangladesh', 'dhaka', 'chittagong', 'sylhet']
    },
    {
        'country': 'Sri Lanka',
        'code': 'LK',
        'symbol': 'Rs',
        'currency_code': 'LKR',
        'currency_name': 'Sri Lankan Rupee',
        'flag': '🇱🇰',
        'keywords': ['sri lanka', 'colombo', 'kandy']
    },
    {
        'country': 'Mexico',
        'code': 'MX',
        'symbol': 'MX$',
        'currency_code': 'MXN',
        'currency_name': 'Mexican Peso',
        'flag': '🇲🇽',
        'keywords': ['mexico', 'mexico city', 'guadalajara', 'monterrey']
    },
    {
        'country': 'Sweden',
        'code': 'SE',
        'symbol': 'kr',
        'currency_code': 'SEK',
        'currency_name': 'Swedish Krona',
        'flag': '🇸🇪',
        'keywords': ['sweden', 'stockholm', 'gothenburg', 'malmo']
    },
    {
        'country': 'Norway',
        'code': 'NO',
        'symbol': 'kr',
        'currency_code': 'NOK',
        'currency_name': 'Norwegian Krone',
        'flag': '🇳🇴',
        'keywords': ['norway', 'oslo', 'bergen']
    },
    {
        'country': 'Denmark',
        'code': 'DK',
        'symbol': 'kr',
        'currency_code': 'DKK',
        'currency_name': 'Danish Krone',
        'flag': '🇩🇰',
        'keywords': ['denmark', 'copenhagen', 'aarhus']
    },
    {
        'country': 'Poland',
        'code': 'PL',
        'symbol': 'zł',
        'currency_code': 'PLN',
        'currency_name': 'Polish Zloty',
        'flag': '🇵🇱',
        'keywords': ['poland', 'warsaw', 'krakow', 'wroclaw', 'gdansk']
    }
]


import re

def detect_currency_from_location(location_str):
    """
    Given a location string (e.g. 'Bangalore, India' or 'London, UK'),
    returns matching country dictionary or None.
    """
    if not location_str or not isinstance(location_str, str):
        return None

    norm = location_str.strip().lower()
    for item in GLOBAL_COUNTRIES_CURRENCIES:
        for kw in item['keywords']:
            if len(kw) <= 3:
                # Use word boundary for short abbreviations like 'us', 'uk', 'usa', 'in'
                if re.search(r'\b' + re.escape(kw) + r'\b', norm):
                    return item
            else:
                if kw in norm:
                    return item
    return None


def get_country_by_currency_symbol(symbol):
    """
    Finds the first matching country by symbol.
    """
    if not symbol:
        return None
    symbol = symbol.strip()
    for item in GLOBAL_COUNTRIES_CURRENCIES:
        if item['symbol'] == symbol or item['currency_code'] == symbol:
            return item
    return None
