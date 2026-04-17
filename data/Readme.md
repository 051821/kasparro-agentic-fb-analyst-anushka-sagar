<!-- Project file: data/Readme.md -->

## Synthetic Facebook Ads Dataset

Facebook Performance Analyst project.

It includes a synthetic Facebook Ads performance CSV designed to mimic real-world advertising metrics while remaining safe, anonymized, and compliant with data policies.
File Included
**Synthetic_fb_ads.csv**

# A synthetic dataset with the following columns:

| **Column Name**   | **Description** |
|-------------------|-----------------|
| `date`            | Daily timestamp for each ad performance entry |
| `campaign_name`   | Name of the Facebook ad campaign |
| `adset_name`      | Name of the ad set |
| `country`         | Target audience country |
| `spend`           | Total money spent on ads that day |
| `impressions`     | Number of times the ad was shown |
| `clicks`          | Number of ad clicks |
| `purchases`       | Number of purchases attributed to the ad |
| `revenue`         | Revenue generated from those purchases |

**Parameters**
1. ctr	Click-Through Rate = clicks / impressions
2. cpc	Cost Per Click = spend / clicks
3. cpm	Cost Per 1000 Impressions
4. roas	Return on Ad Spend = revenue / spend
5. audience_type	Type of target audience (broad, remarketing, lookalike)

# Purpose of This Dataset

- This dataset is created to support:
- Agentic reasoning on marketing analytics,
- ROAS/CTR trend detection,
- Hypothesis generation and evaluation,
- Creative strategy improvement,
- Anomaly detection,
- Multi-agent collaboration,

# Dataset Usage Inside the Project

The dataset is used by:

- *DataAgent* → load and clean data,
- *InsightAgent* → generate hypotheses from patterns,
- *EvaluatorAgent* → validate hypotheses using metrics,
- *CreativeAgent* → propose creative fixes for low CTR / low ROAS,

You can configure dataset usage in:
- config/config.yml
