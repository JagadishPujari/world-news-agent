"""Topic Simplifier tool (FR-4).

Simplifies complex geopolitical, economic, scientific, or global crises concepts
into beginner, intermediate, or expert explanations.
Uses Gemini when keys are present, with a rich mock library fallback.
"""
from __future__ import annotations

from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import get_settings


_MOCK_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "geopolitical conflicts": {
        "beginner": "Geopolitical conflict is like a playground argument between countries, but with real armies and borders. It happens when countries disagree over who owns a piece of land, who gets to make the rules, or how resources like oil are shared. They use talking (diplomacy), trade rules (sanctions), or sometimes physical fighting to get what they want.",
        "intermediate": "Geopolitical conflicts arise from competition between sovereign states or coalitions over strategic territories, resources, trade routes, or ideological influence. These conflicts manifest along a spectrum from diplomatic tensions and economic sanctions (soft power) to proxy wars and direct military engagement (hard power), shaped by historical treaties and alliances like NATO.",
        "expert": "Geopolitical conflict represents a systemic friction point in international relations, characterized by state and non-state actors contesting the distribution of global power. Grounded in structural realism, these conflicts involve security dilemmas where defensive measures by one state are perceived as offensive by rivals. Modern conflicts utilize hybrid warfare, blending cyber-attacks, economic coercion, disinformation campaigns, and asymmetric warfare to shift the balance of power without triggering total war."
    },
    "economic policies": {
        "beginner": "Economic policies are the rules that governments and banks make to manage money. Imagine a family budget: you decide how much to spend, how much to save, and how to earn money. A government does this for the whole country. When prices go up too fast (inflation), they might make it harder to borrow money (raise interest rates) so people spend less, which cools down prices.",
        "intermediate": "Economic policies are divided into fiscal policies (managed by governments via taxing and spending) and monetary policies (managed by central banks via interest rates and money supply). The primary goal is maintaining price stability, full employment, and sustainable GDP growth. For example, during a recession, governments might run a budget deficit to stimulate demand.",
        "expert": "Economic policy frameworks are institutional designs utilizing macroeconomic levers to influence aggregate demand, market structures, and capital allocation. Under Keynesian theory, fiscal policy employs counter-cyclical measures (discretionary spending and progressive taxation) to manage output gaps. Conversely, Monetarist theory dictates that central banks utilize quantitative easing, reserve requirements, and the discount rate to adjust money supply and align inflation with targets."
    },
    "scientific research": {
        "beginner": "Scientific research is like detective work for how the world works. Scientists ask a question, like 'how do cells fight off a virus?', make a guess (hypothesis), and run tests to see if they are right. They write down everything they did so other detectives can try it too, helping us build better medicines, phones, and clean energy.",
        "intermediate": "Scientific research is the systematic investigation into materials and sources in order to establish facts and reach new conclusions. It relies on the scientific method: observation, hypothesis, experimentation, and peer review. Peer review is crucial, meaning independent experts evaluate the work before it is published in journals like Nature.",
        "expert": "Scientific research is an epistemological process leveraging empirical observation and falsifiable hypotheses to expand human knowledge. Rigorous research requires controlling variables, minimizing cognitive bias through double-blind protocols, and establishing statistical significance (e.g., p-values). Dissemination involves rigorous peer-review panels that scrutinize methodology, replicability, and data analysis prior to indexation."
    },
    "global crises": {
        "beginner": "A global crisis is a huge problem that affects almost everyone on Earth and is too big for one country to fix alone. Examples include changing weather patterns (climate change), a sickness spreading everywhere (a pandemic), or a shortage of food. Fixing them requires all countries to work together and share their resources.",
        "intermediate": "Global crises are systemic disturbances that transcend national borders, threatening global security, health, or stability. These crises—such as pandemics, global warming, or financial collapses—have interconnected causes and require multilateral solutions through institutions like the UN or WHO, which are often hindered by national sovereignty conflicts.",
        "expert": "Global crises represent polycrises where distinct systemic risks intersect, amplify one another, and overwhelm institutional mitigation structures. These events exhibit non-linear dynamics, feedback loops, and tipping points (e.g., runaway greenhouse effects or systemic financial contagion). Resolving them requires polycentric governance structures and global public goods provision, which are frequently challenged by free-rider problems and collective action failures."
    }
}


def simplify_topic(topic: str, complexity: str = "beginner") -> str:
    """Explain a complex topic at a specific complexity level (beginner, intermediate, expert).

    Queries Gemini if configured, otherwise falls back to a high-quality pre-written library.
    """
    settings = get_settings()
    complexity = complexity.lower().strip()
    if complexity not in ["beginner", "intermediate", "expert"]:
        complexity = "beginner"

    has_gemini = settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key" and "your_api_key" not in settings.gemini_api_key

    if has_gemini:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            llm = ChatGoogleGenerativeAI(
                google_api_key=settings.gemini_api_key,
                model=settings.gemini_model_name,
                temperature=0.3,
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a master educator. Your task is to explain the requested concept or topic "
                    "in a way that perfectly matches the user's complexity level preference.\n"
                    f"Target Complexity: {complexity.upper()}\n"
                    "- BEGINNER: Use simple analogies, zero jargon, short sentences, and explain like I'm 10 (ELI5).\n"
                    "- INTERMEDIATE: Use clear, standard terms, explain the core concepts, and provide context suitable for a high-school or college student.\n"
                    "- EXPERT: Use precise, professional terminology, address structural/systemic nuances, and provide deep analytical detail."
                )),
                ("user", "Explain the following topic: {topic}")
            ])
            
            chain = prompt | llm | StrOutputParser()
            return chain.invoke({"topic": topic})
        except Exception as e:
            print(f"Gemini topic simplifier failed: {e}. Using mock explanations.")

    # Mock / local explanation fallback
    topic_clean = topic.lower().strip()
    
    # Try finding matching category
    matched_key = None
    for key in _MOCK_EXPLANATIONS.keys():
        # Match if key in topic or topic in key
        if key in topic_clean or topic_clean in key or ("conflict" in topic_clean and key == "geopolitical conflicts") or ("policy" in topic_clean and key == "economic policies") or ("science" in topic_clean and key == "scientific research") or ("crisis" in topic_clean and key == "global crises") or ("climate" in topic_clean and key == "global crises"):
            matched_key = key
            break

    if matched_key:
        return _MOCK_EXPLANATIONS[matched_key][complexity]
        
    # Generic fallback explanation if topic is not pre-defined
    if complexity == "beginner":
        return f"Let's think of '{topic}' like a team project at school. If everyone doesn't talk to each other and share the work fairly, things get confusing and some people get upset. The main thing to know is that it's a complicated topic with many parts, but experts are trying to break it down so we can solve it step-by-step."
    elif complexity == "intermediate":
        return f"The topic '{topic}' is a multifaceted concept that is currently driving discussions in international forums. It involves several stakeholders who have competing interests, and finding a consensus requires balancing immediate needs with long-term strategic goals. Understanding it fully requires looking at both the historical context and the current regulatory frameworks."
    else:  # expert
        return f"An analysis of '{topic}' reveals a highly path-dependent phenomenon governed by systemic incentives and structural constraints. Stakeholders navigate a complex payoff matrix where actions are influenced by game-theoretic dynamics and regulatory oversight. Policy interventions must account for feedback loops and negative externalities to avoid unintended systemic volatility."
