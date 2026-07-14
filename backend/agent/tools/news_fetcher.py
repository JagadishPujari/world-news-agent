"""News retrieval tool (FR-2, FR-3).

Integrates with NewsData.io and CurrentsAPI, and provides a rich mock news
generator fallback if keys are missing or calls fail.
"""
from __future__ import annotations

import datetime
import random
from typing import Any, Dict, List, Optional
import requests

from config import get_settings
from models.responses import NewsItem


# Rich mock news items for each category to ensure high-fidelity demonstration without API keys
_MOCK_NEWS_DATA: Dict[str, List[Dict[str, str]]] = {
    "politics": [
        {
            "title": "Global Leaders Convene in Geneva for International Trade and Security Summit",
            "description": "Heads of state and trade ministers have gathered in Geneva to negotiate new treaties aimed at stabilizing global supply chains and resolving outstanding tariff disputes.",
            "source": "Geneva Herald",
            "url": "https://example.com/politics/geneva-summit",
        },
        {
            "title": "Parliament Approves Historic Electoral Reform Bill After Marathon Session",
            "description": "Following 18 hours of continuous debate, parliament passed the new voting rights and electoral reform bill, changing how districts are drawn and votes counted.",
            "source": "National Gazette",
            "url": "https://example.com/politics/electoral-reform",
        },
        {
            "title": "Senate Committee Launches Inquiry Into Cybersecurity Infrastructure Funding",
            "description": "A bipartisan Senate panel has initiated a comprehensive review of the country's public cybersecurity defenses, calling on technology experts to testify on critical vulnerabilities.",
            "source": "Capitol Chronicle",
            "url": "https://example.com/politics/cybersecurity-inquiry",
        },
        {
            "title": "New Diplomatic Accords Signed to Promote Regional Peace and Cooperation",
            "description": "Four neighboring nations have signed a landmark security pact, pledging mutual intelligence sharing and joint border management initiatives to counter cross-border smuggling.",
            "source": "Regional Diplomat",
            "url": "https://example.com/politics/peace-accords",
        },
        {
            "title": "City Council Unveils Ambitious Urban Housing and Infrastructure Initiative",
            "description": "The mayor's office announced a new $1.2 billion plan to revitalize downtown neighborhoods, build affordable housing units, and expand public transit access.",
            "source": "Metropolitan Post",
            "url": "https://example.com/politics/urban-housing",
        }
    ],
    "sports": [
        {
            "title": "Championship Underdogs Secure Thrilling Victory in Final Seconds",
            "description": "In one of the most stunning upsets in tournament history, the eighth-seeded visitors scored a late goal to claim the league championship trophy.",
            "source": "Sports Illustrated News",
            "url": "https://example.com/sports/championship-upset",
        },
        {
            "title": "Global Tennis Star Announces Retirement After Record-Breaking Career",
            "description": "Holding 24 Grand Slam singles titles, the legendary champion announced that the upcoming US open will be their final competitive tournament.",
            "source": "Court Analytics",
            "url": "https://example.com/sports/tennis-retirement",
        },
        {
            "title": "Track Legend Smashes World Record in 100m Sprint at International Games",
            "description": "Running in near-perfect wind conditions, the 23-year-old sprinter clocked a record-breaking 9.57 seconds, stunning spectators and competitors alike.",
            "source": "Athletics Today",
            "url": "https://example.com/sports/world-record-sprint",
        },
        {
            "title": "New Football League Expansion Teams Confirmed for Upcoming Season",
            "description": "The commissioner's office officially welcomed two new franchises from Chicago and Toronto, expanding the league schedule to 20 total teams next spring.",
            "source": "Gridiron News",
            "url": "https://example.com/sports/league-expansion",
        },
        {
            "title": "Rookie Sensation Dominates Basketball Finals to Claim MVP Honors",
            "description": "Averaging 34 points per game throughout the championship series, the first-year guard led their team to a sweep and took home the Finals MVP trophy.",
            "source": "Hoop Central",
            "url": "https://example.com/sports/rookie-mvp",
        }
    ],
    "technology": [
        {
            "title": "Open-Source AI Consortium Releases Groundbreaking 100B Parameter Model",
            "description": "A coalition of research labs has open-sourced an incredibly capable generative AI model, matching proprietary systems in coding, reasoning, and multi-lingual translation.",
            "source": "TechCrunch Daily",
            "url": "https://example.com/tech/open-source-ai",
        },
        {
            "title": "Breakthrough in Silicon Photonics Promises 10x Faster Data Centers",
            "description": "Researchers have successfully integrated laser-based optical communication directly onto traditional silicon chips, bypassing electronic speed limits in servers.",
            "source": "Silicon Insider",
            "url": "https://example.com/tech/silicon-photonics",
        },
        {
            "title": "Cybersecurity Firmware Defect Exploited in Wild; Patch Issued Immediately",
            "description": "A critical zero-day vulnerability affecting millions of corporate routers was patched today. System administrators are urged to apply the firmware updates immediately.",
            "source": "Wired Security",
            "url": "https://example.com/tech/zero-day-exploit",
        },
        {
            "title": "Quantum Computing Startup Demonstrates Logic Gate with 99.9% Fidelity",
            "description": "By maintaining superconducting qubits at ultra-low temperatures, the hardware developer reached the critical fault-tolerance threshold needed for error correction.",
            "source": "Quantum Journal",
            "url": "https://example.com/tech/quantum-fidelity",
        },
        {
            "title": "Smartphone Manufacturers Unveil Seamless Holographic Display Prototypes",
            "description": "At the annual tech expo, a new generation of mobile displays was demonstrated, allowing users to view 3D holographic content without specialized glasses.",
            "source": "Mobile World",
            "url": "https://example.com/tech/holographic-display",
        }
    ],
    "finance": [
        {
            "title": "Central Bank Holds Interest Rates Steady Amid Cooling Inflation Indicators",
            "description": "In a widely anticipated decision, the Federal Reserve maintained its benchmark lending rate, hinting that rate cuts could begin in the third quarter if trends persist.",
            "source": "Financial Times",
            "url": "https://example.com/finance/rate-decision",
        },
        {
            "title": "Tech Giant Agrees to Historic $45B Acquisition of Leading Semiconductor Firm",
            "description": "In a deal that will reshape the electronics industry, the antitrust division has cleared the way for the largest technology merger of the decade.",
            "source": "Wall Street Journal",
            "url": "https://example.com/finance/megamerger",
        },
        {
            "title": "Global Stock Indices Surge to Record Highs Following Positive Jobs Report",
            "description": "Markets rallied worldwide after labor statistics showed steady job growth and wage stabilization, alleviating fears of an impending recession.",
            "source": "MarketWatch",
            "url": "https://example.com/finance/market-surge",
        },
        {
            "title": "Venture Capital Funding for Clean Energy Startups Doubles in Q2",
            "description": "Investment firms poured a record $8.4 billion into green tech, hydrogen storage, and grid modernization projects as ESG mandates drive institutional capital.",
            "source": "Bloomberg Finance",
            "url": "https://example.com/finance/clean-energy-funding",
        },
        {
            "title": "Retail Sales Outperform Expectations as Consumer Spending Remains Resilient",
            "description": "Despite lingering inflationary pressures, consumer activity in electronics, dining, and travel rose 1.4% last month, indicating strong economic momentum.",
            "source": "Reuters Business",
            "url": "https://example.com/finance/retail-sales",
        }
    ],
    "climate": [
        {
            "title": "Global Climate Conference Secures Binding Pact to Phase Out Coal Subsidies",
            "description": "Delegates from over 190 nations have reached a historic compromise in Kyoto, agreeing to eliminate government funding for coal-fired power stations by 2032.",
            "source": "Kyoto Eco-Review",
            "url": "https://example.com/climate/kyoto-accord",
        },
        {
            "title": "Scientific Study Warns of Accelerating Glacial Melt Rates in Greenland",
            "description": "Satellite telemetry data reveals that Greenland's ice sheets are melting 15% faster than previous models projected, potentially raising sea levels by 1.2 meters by 2100.",
            "source": "Nature Geoscience",
            "url": "https://example.com/climate/greenland-glaciers",
        },
        {
            "title": "Offshore Wind Farm Grid System Commences Operations, Powering 500k Homes",
            "description": "The world's largest array of deep-water wind turbines began feeding electricity into the national grid today, marking a massive milestone for carbon-neutral targets.",
            "source": "Renewable Power",
            "url": "https://example.com/climate/wind-farm",
        },
        {
            "title": "Coral Reef Restoration Project Shows Promising Results in South Pacific",
            "description": "Marine biologists utilizing lab-grown, heat-resistant coral strains have successfully repopulated damaged reefs, showing a 70% survival rate after 18 months.",
            "source": "Oceanic Studies",
            "url": "https://example.com/climate/coral-restoration",
        },
        {
            "title": "Drought-Resilient Genetically Modified Wheat Approved for Commercial Farming",
            "description": "In response to changing rainfall patterns, agricultural regulators have cleared a new wheat variety that maintains yield with 40% less water usage.",
            "source": "AgriScience Journal",
            "url": "https://example.com/climate/drought-wheat",
        }
    ]
}


def _get_mock_news(topic: str, count: int) -> List[NewsItem]:
    """Generate mock news items with dynamic dates for high-fidelity offline runs."""
    topic_key = topic.lower().strip()
    if topic_key not in _MOCK_NEWS_DATA:
        # If the topic isn't exact, pick a random category or try matching substring
        matched = [k for k in _MOCK_NEWS_DATA.keys() if k in topic_key]
        topic_key = matched[0] if matched else "technology"

    templates = _MOCK_NEWS_DATA[topic_key]
    items = []
    
    # Shuffle or select randomly to feel dynamic
    selected = random.sample(templates, min(len(templates), count))
    
    for i, t in enumerate(selected):
        # Generate a realistic date within the last few days
        days_ago = i
        date_str = (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()
        
        items.append(
            NewsItem(
                title=t["title"],
                description=t["description"],
                source=t["source"],
                url=t["url"],
                published_date=date_str,
                category=topic_key,
            )
        )
    return items


def fetch_news(topic: str, count: int = 5) -> List[NewsItem]:
    """Retrieve articles from NewsData.io, CurrentsAPI, or the mock generator fallback.

    Ensures robust handling by falling back to mock news if keys are placeholders
    or if API calls return rate limit/authentication errors.
    """
    settings = get_settings()
    
    # Check if a real key is present
    has_newsdata = settings.newsdata_api_key and settings.newsdata_api_key != "your-newsdata-api-key"
    has_currents = settings.currents_api_key and settings.currents_api_key != "your-currentsapi-key"
    
    # Normalize topic for search query
    query = topic.strip()
    if not query:
        query = "global"

    if settings.news_provider == "newsdata" and has_newsdata:
        try:
            # NewsData.io Integration
            url = "https://newsdata.io/api/1/news"
            params = {
                "apikey": settings.newsdata_api_key,
                "q": query,
                "language": "en",
            }
            # Map known categories to NewsData's structured category filter
            mapped_category = query.lower()
            if mapped_category in ["politics", "sports", "technology", "finance", "climate"]:
                # Map some categories if necessary, newsdata supports: business, entertainment, environment, food, health, politics, science, sports, technology, top, world
                if mapped_category == "finance":
                    params["category"] = "business"
                elif mapped_category == "climate":
                    params["category"] = "environment"
                else:
                    params["category"] = mapped_category

            response = requests.get(url, params=params, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "results" in data:
                    results = data["results"][:count]
                    items = []
                    for r in results:
                        source = r.get("source_id") or "NewsData"
                        pub_date = r.get("pubDate") or datetime.date.today().isoformat()
                        items.append(
                            NewsItem(
                                title=r.get("title") or "Untitled Article",
                                description=r.get("description") or r.get("content") or "",
                                source=str(source).capitalize(),
                                url=r.get("link") or "",
                                published_date=str(pub_date),
                                category=query,
                            )
                        )
                    if items:
                        return items
            print(f"NewsData API returned non-success: {response.text}. Falling back to mock news.")
        except Exception as e:
            print(f"Error calling NewsData.io: {e}. Falling back to mock news.")

    elif settings.news_provider == "currents" and has_currents:
        try:
            # CurrentsAPI Integration
            url = "https://api.currentsapi.services/v1/search"
            headers = {"Authorization": settings.currents_api_key}
            params = {
                "keywords": query,
                "language": "en",
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and "news" in data:
                    results = data["news"][:count]
                    items = []
                    for r in results:
                        source = r.get("author") or "CurrentsAPI"
                        pub_date = r.get("published") or datetime.date.today().isoformat()
                        items.append(
                            NewsItem(
                                title=r.get("title") or "Untitled Article",
                                description=r.get("description") or "",
                                source=str(source),
                                url=r.get("url") or "",
                                published_date=str(pub_date),
                                category=query,
                            )
                        )
                    if items:
                        return items
            print(f"CurrentsAPI returned non-success: {response.text}. Falling back to mock news.")
        except Exception as e:
            print(f"Error calling CurrentsAPI: {e}. Falling back to mock news.")

    # Default fallback to mock news
    return _get_mock_news(query, count)
