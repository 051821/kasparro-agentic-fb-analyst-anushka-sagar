## Agentic Facebook Ads Performance Analyst
## Kasparro — Applied AI Engineer Assignment (by Anushka Sagar)

*This project is my implementation of a multi-agent AI system that behaves like a smart Facebook Ads Performance Analyst.*
It automatically:

Detects why ROAS changed

Finds what caused metric fluctuations

Generates creative messaging ideas for low-CTR ads

Produces a final marketing report

Everything runs end-to-end using LangChain + Ollama (local LLM), making it fully open-source and offline-friendly.

 **Quick Start**
1️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows → venv\Scripts\activate

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Run the system
python src/run.py "Analyze ROAS drop in last 7 days"


That’s it — the system will automatically create:

reports/insights.json

reports/creatives.json

reports/report.md

📂 Project Structure
.
|-- README.md
|-- config/
|   └── config.yml
|-- data/
│   ├── Readme.md
│   └── Synthetic_fb_ads.csv
|-- prompts/
│   ├── Planner.md
│   ├── data_agent_prompt.md
│   ├── insight_agent_prompt.md
│   ├── evaluator_agent_prompt.md
│   ├── creative_generator_prompt.md
│   └── reflection_prompt.md
|-- reports/
│   ├── insights.json
│   ├── creatives.json
│   └── report.md
|-- src/
│   ├── agents/
│   │   ├── planer_agent.py
│   │   ├── data_agent.py
│   │   ├── insight_agent.py
│   │   ├── evaluator_agent.py
│   │   └── creative_agent.py
│   ├── orchestrator/
│   │   └── agent_control.py
│   ├── utils/
│   │   ├── load_data.py
│   │   ├── summary.py
│   │   ├── validate.py
│   │   ├── logger.py
│   │   └── schemas.py
│   └── run.py
|-- tests/
│   ├── test_plan.py
│   ├── test_data.py
│   └── test_evl.py
|-- venv/

📊 Data Instructions

Place your dataset inside the data/ folder:

data/Synthetic_fb_ads.csv


The dataset must include columns like:

spend, impressions, clicks, ctr, purchases, roas

campaign_name, adset_name

platform, country, audience_type

creative_message, creative_type

Update path in config:

config/config.yml:

data_path: "data/Synthetic_fb_ads.csv"
use_sample_data: true
random_seed: 42
confidence_min: 0.6

**Architecture Overview**

Below is the agent workflow that my system uses:

1. *Planner Agent*
*(load data → analyze → evaluate → generate creatives)*

2. *Data Agent*
Loads the Facebook Ads CSV file
Calculates high-level summaries such as:
Spend totals
CTR trends
ROAS changes
Purchase volume

3. *Insight Agent*
*Looks at the dataset summary Generates hypotheses explaining performance changes*

4. *Evaluator Agent*

*Validates each hypothesis using real metrics*
Computes:
ROAS difference
CTR change
Spend / Purchase variation
Assigns a final confidence score for each hypothesis

5. *Creative Generator Agent*

Finds campaigns with low CTR
Suggests better creative ideas using LLM + existing messaging

Outputs:
New headlines
Hooks
CTAs

Visual suggestions

6.*Report Generator (Final Output)*
Combines everything into:
*insights.json
creatives.json
report.md (final marketing report)*

**✔ Validation Logic (Evaluator Agent)**

To make insights believable, the evaluator agent uses:

1. ROAS Change Validation
Compares selected time window with previous
Computes percentage change

2. CTR + Frequency Checks
If CTR ↓ but frequency ↑ → audience fatigue

3. Confidence Score
Each hypothesis gets a final score based on:
ROAS change (40%)
CTR change (30%)
Purchase volume change (30%)
Scores are deterministic using the config seed.

## Example Outputs
*insights.json*
[
  {
    "id": "HYP-1",
    "hypothesis": "ROAS dropped due to rising frequency causing audience fatigue.",
    "confidence": 0.76,
    "evidence": ["CTR dropped -18%", "Frequency increased from 2.1 to 4.3"]
  }
]

 *creatives.json*
[
  {
    "campaign": "Winter Sale",
    "suggestions": [
      "Add scarcity-driven headline",
      "Use lifestyle imagery with product in use",
      "Short vertical UGC-style video"
    ]
  }
]

📄 report.md 
## Key Findings
ROAS fell by -21% in the last 7 days. Two major factors contributed:
- Audience fatigue from repeated creatives
- Weak headline engagement in high-frequency ad sets

## Creative Recommendations
- Use more benefit-led messaging
- Try FOMO hooks like "Ends Tonight"
- Use variant with human model in frame

**Testing**

Run all tests:
pytest -q

Tests cover:
Planner fallback logic
Dataset loading
Evaluator scoring

**Makefile**
make install
make run
make test


**Tech Stack**
Python 3.12
LangChain (agents, prompts)
Ollama (local LLM inference)
Pandas / NumPy
Loguru for logs
PyTest for automated tests
