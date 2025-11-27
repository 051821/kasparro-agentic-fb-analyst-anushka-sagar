
Agentic Facebook Performance Analyst

A Multi-Agent System for Diagnosing ROAS Fluctuations & Generating Creative Recommendations

📌 1. Project Summary

This project builds an Agentic AI System capable of autonomously analyzing Facebook Ads performance.
Given any marketer’s query such as:

“Analyze ROAS drop in last 7 days”

the system performs a fully automated pipeline:

Understands the query

Loads & summarizes data

Generates hypotheses for ROAS change

Validates them quantitatively

Creates improved ad creatives for low-CTR segments

Produces a final structured report

It demonstrates how LLMs + LangChain + multi-agent workflows can replicate a real Marketing Performance Analyst.

🧠 2. Core Capabilities
✔ Diagnose ROAS change

Identifies why ROAS increased or decreased using signals like:

CTR drop

High impressions but low clicks

Audience fatigue

Underperforming creatives

Country-level performance issues

Spend scaling inefficiencies

✔ Generate analytical hypotheses

Agents use dataset summaries to form grounded insights, not hallucinated ones.

✔ Validate hypotheses

Quantitative evaluation using:

ROAS before vs after time window

Spend vs revenue ratio

CTR changes

Purchase trends

✔ Recommend new creatives

LLM proposes:

3–5 new headlines

CTA improvements

Messaging variations

Hooks based on past creative themes

⚙️ 3. Technology Stack
Component	Purpose
Python 3.10+	Core runtime
LangChain	Prompting, output parsing, agent modules
Ollama	Local LLM inference (Llama 3 / Mistral / Llama 2)
Pandas	Data processing
PyYAML	Config loading
Loguru	Logging
pytest	Testing

The system runs fully locally, no API keys or paid cloud required.

📁 4. Project Structure
.
|-- README.md
|-- config
|   `-- config.yml
|-- data
|   |-- Synthetic_fb_ads.csv
|-- prompts
|-- reports
|-- requirements.txt
|-- src
|   |-- agents
|   |-- orchestrator
|   |-- run.py
|   `-- utils
|-- tests


Everything is cleanly modularized for easier evaluation.

🔷 5. Multi-Agent Architecture

The system contains five autonomous agents, each with a clear responsibility.

🧩 (A) Planner Agent

📌 Responsible for:
Understanding the user query and converting it into a structured JSON task plan.

📤 Outputs include:

Task type

Time window

Steps to execute

Filters (campaign/country/audience)

This provides a deterministic structure that the entire workflow follows.

🗂 (B) Data Agent

📌 Responsible for:
Loading CSV → applying filters → generating dataset summary.

It produces:

Total spend, clicks, revenue

CTR & ROAS calculations

Creative performance buckets

Audience-level stats

This summary is passed to the Insight Agent.

🔍 (C) Insight Agent

📌 Responsible for:
Using the summary to generate hypotheses explaining ROAS fluctuations.

Example hypotheses:

“ROAS declined due to CTR dropping 22% in retargeting.”

“Audience fatigue from repeated creatives.”

“Spend scaled too quickly without incremental revenue.”

Outputs strict JSON with:

ID

Description

Expected signals

Affected segment

📈 (D) Evaluator Agent

📌 Responsible for:
Validating each hypothesis using the original dataset.

Evaluation includes:

ROAS before vs after

CTR delta

Spend/Reveune slope

Confidence scoring

Produces:

{
  "id": "H1",
  "confidence": 0.72,
  "evidence": { ... }
}

🎨 (E) Creative Generator Agent

📌 Responsible for:
Generating new creative concepts for low-CTR segments.

Based on:

Past creative_message column

Campaign themes

Low-performing audience segments

Output includes:

Headlines

Hooks

CTAs

Messaging improvements

🔗 6. Full Workflow (Step-by-Step)

Here’s how the system runs from start to finish:

1️⃣ User Query

Example:

"Analyze ROAS drop in last 7 days"

2️⃣ Planner Agent

Converts query → JSON plan:

{
  "task": "analyze_roas_change",
  "steps": [...],
  "focus": {
     "time_window": "last_7_days"
  }
}

3️⃣ Data Agent

Loads CSV, filters by the planner, and prepares summary:

total spend

country-level performance

creative CTRs

segment breakdown

ROAS per adset

4️⃣ Insight Agent

Reads the summary → produces hypotheses:

H1: CTR dropped -18% in US audience
H2: Creative fatigue on carousel ads

5️⃣ Evaluator Agent

Validates each hypothesis:

statistical differences

CTR drop computation

ROAS time-series

confidence score

6️⃣ Creative Generator Agent

Uses the insights + low-performing creatives to generate:

new hooks

message angles

CTAs

ad copy variants

7️⃣ Report Generator

Combines all results into:

insights.json

creatives.json

final report.md

📜 7. Architecture Diagram (Mermaid)
flowchart TD

A[User Query] --> B[Planner Agent]
B --> C[Data Agent]
C --> D[Insight Agent]
D --> E[Evaluator Agent]
E --> F[Creative Generator Agent]
F --> G[Report Builder]

C -->|Summary Data| D
D -->|Hypotheses| E
E -->|Validated Insights| F
F -->|Creative Ideas| G

▶️ 8. Running the System
Basic command:
python src/run.py "Analyze ROAS drop in last 7 days"

Output saved in:
reports/insights.json
reports/creatives.json
reports/report.md

🧪 9. Testing

Run all tests:

pytest -q


Includes:

planner logic

data load + summary

hypothesis evaluation