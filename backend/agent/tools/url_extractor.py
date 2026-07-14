"""URL extraction tool (FR-6.2 / Route 2).

Fetches web pages, extracts primary text content using BeautifulSoup, and cleans
it of navigation/boilerplate. In offline/mock mode or on failure, it returns high-fidelity
full articles corresponding to mock news stories.
"""
from __future__ import annotations

import re
from typing import Dict
import requests
from bs4 import BeautifulSoup


_MOCK_ARTICLES: Dict[str, str] = {
    "geneva-summit": (
        "GENEVA — The annual International Trade and Security Summit opened today in Geneva, Switzerland, "
        "with leaders from over forty nations in attendance. The summit is taking place amid rising tensions "
        "in global commerce and shipping lanes. Keynote addresses from the host nation highlighted the "
        "critical necessity of shielding vital supply chains from geopolitical disputes. 'We cannot allow the "
        "movement of essential goods, food, and technology to be held hostage by regional disputes,' declared "
        "the chairperson in her opening statement. Negotiations are currently underway behind closed doors to draft "
        "a multilateral accord on tariff reductions and cybersecurity protections for trade infrastructure. "
        "Delegates express cautious optimism that a consensus on tariff stabilization can be reached by Friday."
    ),
    "electoral-reform": (
        "NATIONAL CAPITOL — Following an intense, 18-hour continuous debate, parliament has officially passed "
        "the Electoral Reform and Representation Act. The new legislation, which has sparked intense debate, "
        "redefines the process by which voting districts are outlined and registered. Supporters argue that the "
        "amendments will prevent gerrymandering and guarantee that minority representation is preserved. "
        "Opponents, however, claim the reforms could lead to administrative delays during municipal elections. "
        "The bill also allocates $150 million to modernize voting booth technology and establish electronic "
        "registration systems. The changes are slated to take effect in the upcoming midterm cycle."
    ),
    "open-source-ai": (
        "SILICON VALLEY — A coalition of prominent academic institutions and independent research facilities "
        "has announced the release of 'Aether-100B,' a new open-source large language model boasting 100 billion parameters. "
        "The project, which was funded by non-profit grants, represents a major challenge to the proprietary AI models "
        "developed by technology conglomerates. According to the benchmark data released alongside the weights, Aether-100B "
        "matches commercial engines in complex multi-step reasoning, mathematical problem solving, and Python programming. "
        "By distributing the model weights freely under an Apache 2.0 license, the consortium hopes to enable researchers "
        "worldwide to study model alignment, bias mitigation, and architectural optimizations without expensive api overhead."
    ),
    "rate-decision": (
        "WASHINGTON — The Federal Reserve Board of Governors has voted unanimously to hold the target range for the "
        "federal funds rate steady at 5.25 to 5.50 percent. In the accompanying policy statement, the central bank noted "
        "that while inflation has cooled significantly over the past two quarters, it remains slightly above the long-term "
        "target of 2.0 percent. 'The economic outlook remains resilient, with strong job growth and steady consumer demand,' "
        "the Chairman stated during the press conference. Financial analysts interpret the decision as a sign that the Fed "
        "is waiting for further confirmation of price stability before initiating rate cuts, which are widely projected to "
        "commence at the September meeting."
    ),
    "kyoto-accord": (
        "KYOTO — Representatives from 192 nations concluded the UN Climate Action Conference by signing the Kyoto Clean Energy "
        "and Subsidy Transition Accord. Under the terms of the binding treaty, signatory nations are required to phase out "
        "all direct government subsidies for coal-fired power plants by the year 2032. Developed nations have also committed "
        "to contributing $100 billion annually to a transition fund, which will assist developing economies in building out "
        "their solar, wind, and geothermal infrastructure. The agreement represents the first time that nations have agreed to "
        "legally binding timelines for the elimination of fossil fuel subsidies, representing a major breakthrough in international "
        "climate diplomacy."
    )
}


def extract_content(url: str) -> str:
    """Fetch URL and extract primary text. Falls back to mock articles if needed."""
    url_clean = url.strip()
    if not url_clean:
        return "Empty URL provided."

    # Check if this matches a mock URL
    for key, content in _MOCK_ARTICLES.items():
        if key in url_clean:
            return content

    # If it is a generic example.com/google.com/etc. or mock URL, return a friendly placeholder
    if "example.com" in url_clean or "localhost" in url_clean:
        return (
            f"This is the extracted content from the URL: {url_clean}. "
            "In a live deployment, our system connects to the web server, retrieves the HTML document, "
            "strips away the header, footer, sidebar navigation, and advertisement scripts using BeautifulSoup, "
            "and presents only the clean article body for LLM processing."
        )

    # Real web scraping attempt
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url_clean, headers=headers, timeout=8)
        if response.status_code != 200:
            return f"Failed to retrieve URL. Server returned status code: {response.status_code}"

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, "lxml")

        # Strip scripts, styles, nav, footer, header
        for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
            element.decompose()

        # Try to find common article containers
        article = soup.find("article")
        if article:
            text = article.get_text()
        else:
            # Fallback to main body or paragraphs
            body = soup.find("body")
            if body:
                text = body.get_text()
            else:
                text = soup.get_text()

        # Clean whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_clean = "\n".join(chunk for chunk in chunks if chunk)

        # Truncate to reasonable size (e.g. 5000 characters) for LLM
        return text_clean[:5000]

    except Exception as e:
        return f"Error extracting content from URL '{url_clean}': {str(e)}. Please verify the URL or try another source."
