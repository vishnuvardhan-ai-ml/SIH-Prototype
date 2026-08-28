# Synthetic Dataset Documentation

> [!WARNING]
> **SYNTHETIC / DEMO DATA DISCLOSURE**:
> All records in `sample-data/synthetic_dataset.csv` are synthetically generated for initial prototyping, testing, and architecture validation in the SIH 2026 project. This dataset does **NOT** represent actual government records, confidential project documents, or real-world project telemetry. Model performance metrics trained on this synthetic data serve purely as algorithmic proof-of-concept and do not imply real-world predictive precision.

---

## 1. Feature Dictionary

| Feature Name | Type | Realistic Range | Description |
|---|---|---|---|
| `project_id` | String | `PRJ-SYNTH-XXXXX` | Unique identifier assigned to each project assessment record. |
| `project_type` | Categorical | `Highway`, `Railway`, `Urban Infrastructure`, `Energy & Power`, `Industrial Corridor` | Infrastructure project vertical. |
| `land_area` | Integer | $10 - 3,500$ acres | Total land parcel acreage required for project execution. |
| `affected_families` | Integer | $0 - 5,000$ | Number of families/landowners displaced or affected needing R&R compensation. |
| `legal_disputes` | Integer | $0 - 30+$ | Count of pending court cases, injunctions, or land title disputes. |
| `pending_approvals` | Integer | $0 - 15$ | Number of pending statutory, forest, wildlife, or municipal clearances. |
| `compensation_percent` | Integer | $0 - 100\%$ | Proportion of compensation disbursed to land title holders. |
| `rr_progress_percent` | Integer | $0 - 100\%$ | Rehabilitation and Resettlement (R&R) physical progress. |
| `possession_percent` | Integer | $0 - 100\%$ | Percentage of land parcel area physically acquired and in authority possession. |
| `environmental_clearance` | Categorical | `APPROVED`, `IN_REVIEW`, `PENDING`, `REJECTED` | Environmental & Forest clearance status. |

---

## 2. Target Variables

| Target Variable | Type | Range | Description |
|---|---|---|---|
| `risk_score` | Integer | $0 - 100$ | Composite risk score evaluating the overall risk profile. |
| `risk_category` | Categorical | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Risk band for priority triage (`LOW`: 0-34, `MEDIUM`: 35-59, `HIGH`: 60-79, `CRITICAL`: 80-100). |
| `delay_probability` | Float | $0.00 - 1.00$ | Sigmoidal probability that the land acquisition will encounter critical schedule overrun. |
| `predicted_delay_days` | Integer | $0 - 600$ days | Estimated timeline overrun in days. |
| `is_delayed` | Binary | $0$ or $1$ | Indicator if delay exceeds baseline milestone thresholds. |

---

## 3. Synthetic Generation Methodology

The synthetic data generation follows domain heuristics reflecting standard infrastructure project management dynamics:
1. **Project Type Distribution**:
   - Highway ($35\%$), Railway ($25\%$), Urban Infrastructure ($20\%$), Energy & Power ($10\%$), Industrial Corridor ($10\%$).
2. **Land Area & Population Density**:
   - Area sampled from a Gamma distribution parameterized by project vertical.
   - Affected families modeled via a Poisson distribution proportional to acreage and urban density multipliers.
3. **Disputes & Approval Bottlenecks**:
   - Litigation intensity rises non-linearly with population density per acre and lower initial compensation.
4. **Milestone Correlations**:
   - Land possession cannot outpace compensation disbursal and R&R completion.
5. **Target Risk Scoring Formula**:
   $$\text{Raw Risk} = 3.8 \cdot \text{disputes} + 4.2 \cdot \text{approvals} + 0.4 \cdot \text{env\_penalty} + 0.25 \cdot (100 - \text{comp}\%) + 0.22 \cdot (100 - \text{rr}\%) + 0.28 \cdot (100 - \text{possession}\%) + 2.2 \cdot \ln(1 + \text{families}) + \epsilon$$
   $$\text{delay\_probability} = \sigma\left(\frac{\text{risk\_score} - 48}{12}\right)$$

---

## 4. Assumptions and Limitations
- **Assumptions**: Clearances, compensation, and legal disputes are the primary drivers of land acquisition bottlenecks.
- **Limitations**: Does not capture macroeconomic shocks, state-level legal variances, or seasonal weather disruptions.
- **Data Replacement**: To swap in real government project data, format the incoming table with matching column headers and re-run `ml/training/train.py`.
