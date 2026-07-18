# AURRA Predictive Maintenance Model Card

*A.04 · Model Transparency Document · Google Model Card Format*

Transparency documentation for the machine learning model powering AURRA's predictive HVAC maintenance system. Covers model architecture, training data, performance metrics, known limitations, and fairness considerations.

- **Precision:** 0.91
- **Recall:** 0.84
- **F1 Score:** 0.87
- **Alert Threshold:** 0.72

## 01 · Model Details

| Field | Value |
|---|---|
| Model Name | AURRA Predictive Maintenance Model |
| Model ID | `aurra-pm-xgb-v1.2` |
| Version | 1.2 (April 2026) |
| Model Type | Gradient Boosted Decision Tree (XGBoost) ensemble with time-series feature engineering |
| Task | Multi-class classification: predict HVAC component failure type and urgency from sensor telemetry |
| Framework | XGBoost 2.0 with scikit-learn preprocessing pipeline |
| Inference | REST API endpoint `/predictive/hvac/{device_id}/status` |
| License | Proprietary. Model weights not distributed. Inference via AURRA API only. |
| Compute | ~18 kg CO₂e (training) · Inference: 12ms @ AWS c6i.xlarge |
| Owner | AURRA ML Engineering |
| Contact | ml-team@aurrahome.com |

## 02 · Intended Use

**Primary intended use:** Predict residential HVAC component failures 7 to 21 days before breakdown, based on vibration telemetry and energy consumption patterns. The model outputs a failure category, a confidence score (0.0 to 1.0), and a recommended action for the homeowner or service technician.

**Primary intended users:** AURRA platform integrators (via the REST API), HVAC service providers receiving automated dispatch alerts, and homeowners receiving maintenance recommendations through the AURRA mobile app.

**Downstream applications:** Alert dispatch automation (triggered at the platform default confidence threshold of 0.72), technician scheduling systems, and energy efficiency reporting dashboards.

> **Out-of-Scope Uses:** This model is not designed or validated for: commercial or industrial HVAC systems, geothermal heat pump configurations, HVAC units older than 15 years (see Limitations), real-time safety-critical shutdown decisions, or medical/clean-room environmental control. The model produces advisory predictions and should not serve as the sole basis for emergency HVAC shutoff.

## 03 · Model Architecture

The model uses a two-stage architecture. The first stage is a feature engineering pipeline that transforms raw sensor telemetry into time-series features: rolling window statistics (mean, standard deviation, peak-to-peak) over 1-hour, 6-hour, and 24-hour windows for both vibration and energy inputs, plus derived features including vibration trend slope, energy consumption rate-of-change, and duty cycle ratio.

The second stage is an XGBoost multi-class classifier (5 failure categories + 1 healthy class) trained on the engineered feature set. The ensemble uses 500 estimators with a maximum depth of 8, trained with a learning rate of 0.05 and early stopping at 50 rounds. Class weights are balanced to account for the natural imbalance between healthy readings and failure events.

Confidence scores are derived from the model's softmax probability for the predicted failure class. The platform default alert threshold of 0.72 was calibrated via cost-sensitive analysis where false negatives (missed failures, avg. cost $850 USD including emergency repair and secondary damage) were weighted 3.2x higher than false positives ($265 USD per unnecessary truck roll). This weighting optimizes the precision-recall trade-off for residential maintenance scheduling.

> **Threshold Configurability:** Integrators can override the default 0.72 threshold via the `/alerts` endpoint's `confidence` parameter. Lowering the threshold increases recall (fewer missed failures) at the cost of precision (more false alerts). See Section 06 for threshold-specific metrics.

**Feature importance:** SHAP (SHapley Additive exPlanations) analysis of mean absolute contribution identifies `current_amps` (24%), `amplitude_24h_mean` (18%), and `duty_cycle_ratio` (15%) as primary failure predictors. Voltage deviation contributes 8% but shows high interaction effects with climate zone 5A (cold-weather electrical stress). Full SHAP visualizations are available via the model registry.

## 04 · Training Data

| Field | Value |
|---|---|
| Dataset | AURRA Residential Telemetry Corpus v3 |
| Collection Period | October 2023 through March 2026 (30 months) |
| Source Devices | 14,200 residential HVAC units across the continental United States |
| Total Readings | ~248M telemetry records (vibration + energy) |
| Failure Events | 18,430 confirmed failure events (technician-verified within 30 days of prediction window) |
| Labeling | Failure labels assigned by cross-referencing telemetry anomalies with service records from 42 HVAC maintenance partners |
| Train / Val / Test | 70% / 15% / 15% split. Temporal: test set uses the most recent 3 months to prevent data leakage. |
| Anonymization | All device IDs, geolocation, and homeowner data stripped before training. Only sensor readings and HVAC system metadata retained. |

**Geographic distribution:** Training data covers ASHRAE climate zones 2A through 6A, with highest density in zones 3A (Southeast), 4A (Mid-Atlantic), and 5A (Upper Midwest). Zones 7 and 8 (subarctic) are not represented.

**HVAC system types:** Split-system central air (62%), heat pump (24%), packaged unit (11%), ductless mini-split (3%). Window units and portable systems are excluded.

> **Data Freshness:** The model is retrained quarterly as new telemetry and service records accumulate. Version 1.2 includes winter 2025-2026 heating season data, which improved cold-weather failure detection. See the changelog at `docs.aurrahome.com/ml/changelog`.

## 05 · Input Features

The model ingests two telemetry streams from the AURRA sensor array. Raw readings are transformed into 23 engineered features before classification.

| Stream | Feature | Description | Type |
|---|---|---|---|
| Vibration Telemetry | amplitude | Peak vibration in g-force from the MEMS accelerometer mounted on the compressor housing. | float · range: 0.0 to 10.0 g |
| Vibration Telemetry | frequency | Dominant vibration frequency in Hz, extracted via FFT from the raw accelerometer signal. | float · Hz |
| Vibration Telemetry | duration_ms | Sample window length in milliseconds. Longer windows improve frequency resolution at the cost of latency. | integer · default: 1000 ms |
| Energy Telemetry | runtime_mins | HVAC compressor runtime in minutes for the reporting period. Used to derive duty cycle and efficiency metrics. | integer · minutes |
| Energy Telemetry | voltage | Supply voltage at the HVAC disconnect. Deviations from nominal indicate electrical supply issues. | float · volts |
| Energy Telemetry | current_amps | Current draw in amperes. Elevated draw relative to runtime signals motor bearing wear and capacitor degradation. | float · amperes |

**Derived features (23 total):** Rolling window statistics (1h, 6h, 24h) for amplitude, frequency, and current draw. Vibration trend slope over 72-hour windows. Energy consumption rate-of-change. Duty cycle ratio (runtime / elapsed time). Voltage deviation from 30-day rolling mean. Amplitude-frequency interaction term. Current-to-runtime efficiency ratio.

## 06 · Performance Metrics

Metrics evaluated on the held-out test set (most recent 3 months, 2,764 confirmed failure events). All metrics reported at the platform default alert threshold of 0.72 unless noted.

**Aggregate metrics at threshold 0.72**

| Metric | Value |
|---|---|
| Precision | 0.91 |
| Recall | 0.84 |
| F1 Score | 0.87 |
| AUC-ROC | 0.94 |

**Threshold sensitivity analysis**

| Threshold | Precision | Recall | F1 | FP Rate | Use Case |
|---|---|---|---|---|---|
| 0.50 | 0.78 | 0.93 | 0.85 | 8.2% | High-recall: minimize missed failures |
| 0.60 | 0.84 | 0.90 | 0.87 | 5.6% | Balanced: warranty programs |
| 0.72 (platform default) | 0.91 | 0.84 | 0.87 | 3.1% | Platform default |
| 0.85 | 0.95 | 0.72 | 0.82 | 1.4% | High-precision: minimize false alerts |
| 0.95 | 0.98 | 0.51 | 0.67 | 0.4% | Conservative: high-certainty only |

## 07 · Subgroup Performance

**Performance by failure category** at threshold 0.72. The model performs best on compressor and capacitor failures, which produce the most distinctive telemetry signatures. Refrigerant leak detection has the lowest recall due to subtler signal patterns.

| Failure Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Compressor bearing degradation | 0.94 | 0.89 | 0.91 | 842 |
| Capacitor degradation | 0.93 | 0.88 | 0.90 | 614 |
| Blower motor anomaly | 0.90 | 0.83 | 0.86 | 521 |
| Heat exchanger fouling | 0.88 | 0.80 | 0.84 | 448 |
| Refrigerant leak indicators | 0.85 | 0.74 | 0.79 | 339 |

**Performance by HVAC system type**

| System Type | F1 | Training % | Note |
|---|---|---|---|
| Split-system central air | 0.89 | 62% | Highest representation, strongest signal |
| Heat pump | 0.86 | 24% | Dual-mode operation widens the feature space |
| Packaged unit | 0.83 | 11% | Lower representation limits generalization |
| Ductless mini-split | 0.76 | 3% | Underrepresented; use with caution |

> **Representation & Performance:** Model performance correlates with training data representation. The F1 gap between split-system (0.89) and ductless mini-split (0.76) reflects the 62% vs. 3% data ratio. Integrators deploying to mini-split-heavy populations should raise the alert threshold to 0.85 to maintain acceptable precision.

## 08 · Limitations & Known Issues

> **Critical Limitation:** Not validated for HVAC units older than 15 years. Older systems produce vibration signatures outside the training distribution. Prediction confidence for these units is unreliable. Integrators should flag units installed before 2010 and present predictions with an explicit age disclaimer.

**Geothermal systems:** Zero training data for geothermal heat pump configurations. Predictions for geothermal units will be inaccurate. The API does not reject requests from geothermal devices, so integrators must filter at the application layer.

**Climate zone gaps:** ASHRAE zones 7 and 8 (subarctic, arctic) are absent from training data. Units in these zones may exhibit cold-weather patterns the model has not learned. Version 1.2 extended coverage through zone 6A but not beyond.

**Refrigerant leak detection:** Lowest recall (0.74) because leaks produce gradual efficiency degradation rather than distinct vibration anomalies. Detection relies on energy consumption rate-of-change, which seasonal temperature shifts can confound. Supplement with direct pressure sensor data where available.

**Cold-start period:** Minimum 72 hours of telemetry required from a newly installed device before predictions reach rated accuracy. During cold-start, rolling window features lack sufficient history. Suppress predictions or flag as low-confidence.

**Sensor calibration drift:** MEMS accelerometers can drift in high-vibration environments. The model does not self-correct for drift. Implement annual calibration checks and flag devices where amplitude baseline has shifted more than 15% from installation readings.

## 09 · Ethical Considerations & Fairness

**Demographic fairness:** This model operates on mechanical sensor data only. No demographic, household income, geographic, or personally identifiable information is used as a model input or training feature. The model excludes demographic features by design, preventing disparate impact based on homeowner characteristics.

**Geographic equity concern:** Training data concentrates in ASHRAE zones 2A through 6A, with higher density in suburban installations. Rural and extreme-climate homes are underrepresented, creating a coverage gap where those homeowners may receive less reliable predictions. The quarterly retraining cycle addresses this progressively as the fleet expands.

**Economic impact of false predictions:** False positives trigger unnecessary service calls with direct cost to homeowners. False negatives cause unexpected breakdowns. The 0.72 threshold was calibrated with input from the AURRA Customer Advisory Board to balance these costs for median-income residential users. Integrators serving cost-sensitive populations may raise the threshold to reduce false-positive expenses.

**Automation bias risk:** Homeowners and technicians may over-rely on predictions and skip manual inspections. All alert messaging includes: "This is a predictive advisory. A qualified HVAC technician should confirm this finding before repair work begins." Integrators must preserve this advisory framing.

**Data retention:** Raw telemetry retained 24 months for retraining, then aggregated and anonymized. Homeowners can request deletion via the AURRA Privacy Center. Deleted data is excluded from future training within 30 days.

## 10 · Recommendations for Integrators

**Threshold selection:** Start with 0.72. Monitor false positive rates for your user population over the first 90 days and adjust. Warranty programs may benefit from 0.60 to maximize recall. Automated dispatch should use 0.85 or higher.

**Cold-start handling:** Suppress predictions for the first 72 hours after device installation. Display a "Calibrating" state rather than showing low-confidence predictions that could erode trust.

**Mini-split deployments:** If your fleet exceeds 20% ductless mini-splits, contact AURRA ML Engineering for custom threshold calibration or a two-model ensemble strategy. The default threshold may produce unacceptable false positive rates.

**Alert UX requirements:** Always display confidence scores alongside predictions. Always include advisory language. Never present predictions as diagnoses. Use "AURRA detected a pattern consistent with [issue]" rather than "Your [component] is failing."

**Feedback loop:** Submit confirmed outcomes via `POST /diagnostics/feedback`. This data directly improves future versions. Participating integrators receive early access to model updates.

> **Version History**
> - **v1.2 (April 2026):** Added winter 2025-26 heating data. Improved heat exchanger fouling recall from 0.73 to 0.80. Added voltage deviation feature.
> - **v1.1 (January 2026):** Expanded training set from 9,800 to 14,200 devices. Improved ductless mini-split F1 from 0.68 to 0.76.
> - **v1.0 (October 2025):** Initial production release. 5 failure categories. XGBoost architecture.

### About This Documentation

This model card follows emerging ML documentation standards (Google Model Card Toolkit, NeurIPS reproducibility checklists), adapted for HVAC predictive maintenance. I developed the schema to balance technical transparency for integrators with actionable risk disclosures for downstream decision-makers.
