# A Hybrid Mamba-2 Forecaster for On-Device Anomaly Detection

**Patrick Galyen**
Independent Research

---

## Abstract

We present a **hybrid Mamba-2 structured state-space forecaster** for detecting anomalies in continuous time-series data on consumer CPU hardware — with no cloud dependency and no labeled attack or failure data required for training. The model learns a baseline of normal behavior and flags deviations as forecast error (surprise score).

We validate the architecture in two domains:

1. **Vigilo (IoT network security):** A ~1.3M-parameter model trained only on benign traffic detects **75% of infected devices at 1% false-positive rate** on the IoT-23 dataset (20 malware families), catching all loud attacks (port scans, DDoS, noisy botnets) while running entirely on CPU.

2. **Predictive maintenance (PdM):** The same forecaster backbone applied to NASA C-MAPSS turbofan telemetry achieves **100% detection at 1% FPR** on single-operating-condition subsets (FD001, FD003), with median early warning of 54–60 cycles before failure.

Both systems train in minutes on CPU and keep all data local. Vigilo is released as open source at https://github.com/pgalyen1987/Vigilo.

---

## 1. Introduction

Connected devices and industrial equipment generate continuous telemetry, but most organizations cannot send that data to the cloud for analysis — due to privacy, air-gapped environments, bandwidth limits, or regulatory constraints. Signature-based intrusion detection fails against novel malware; rule-based maintenance thresholds require expert tuning per asset.

We pursue **behavioral anomaly detection**: learn what "normal" looks like from benign data alone, then alert when behavior deviates. The core challenge is doing this with a model small enough to run on a network appliance or edge device, fast enough for operational use, and general enough to adapt across input types.

Our contributions:

1. **A compact hybrid Mamba-2 forecaster** (~1.3M parameters) combining Mamba-2 SSD blocks, sparse window attention, and Mixture-of-Experts feed-forward layers — designed for O(1) memory per timestep on long sequences.

2. **Vigilo**, an on-device IoT network anomaly detector evaluated on IoT-23 with honest benchmark methodology.

3. **A predictive-maintenance adaptation** on NASA C-MAPSS with per-asset baseline normalization, defining a clear operating envelope for deployable vs. future-work scenarios.

---

## 2. Forecaster Architecture

The forecaster is a sequence model that predicts the next behavioral window from history. Anomaly score = prediction error.

### 2.1 Core Design

| Parameter | Value |
|-----------|-------|
| Total parameters | ~1.3M |
| d_model | 128 |
| Layers | 4 (2 Mamba-2 + 2 sparse attention) |
| MoE experts | 4, top-2 routing |
| Attention window | 512 |
| Training hardware | CPU (~1 minute per dataset) |

**Mamba-2 SSD blocks** provide O(1) state memory per timestep, making long behavioral histories tractable without growing KV cache.

**Sparse window attention** handles local pattern structure (short-term correlations in traffic or sensor readings).

**MoE FFN** increases expressiveness without proportional compute cost.

### 2.2 Scoring

For each asset (IoT device or engine):

1. Extract fixed-size feature windows from telemetry.
2. Forecast the next window from prior history.
3. Compute surprise = error between forecast and observed behavior.
4. Flag windows exceeding a threshold calibrated on benign data at target FPR.

Vigilo adds a dedicated **beaconing detector** (inter-arrival interval regularity) to catch stealthy periodic C2 channels that volume-based scoring may miss.

---

## 3. Vigilo — IoT Network Anomaly Detection

### 3.1 Problem and Approach

IoT devices communicate in patterns alien to traditional IT monitoring: periodic telemetry, MQTT pub/sub, UPnP discovery. Endpoint agents cannot be installed on a smart thermostat. Network-level behavioral baselining is the practical defense.

Vigilo reads Zeek `conn.log` files (or converts pcap via tshark), groups traffic into **5-minute behavioral windows per device** (15 features: connection counts, byte volumes, port entropy, protocol ratios, timing), and scores forecast error.

### 3.2 IoT-23 Benchmark Results

Trained on benign honeypot captures (29 benign devices). Evaluated on every malware family in IoT-23:

| Metric | Value |
|--------|-------|
| Detection @ ~1% FPR | **75% (15/20 infected devices)** |
| Benign baseline (device peak) | p95 = 1.93, max = 1.97 |
| Training data | Benign traffic only |
| Model | ~1.3M params, CPU, fully local |

**What it catches:** Loud attacks — port scans, DDoS/flooding, noisy botnet C&C (scores 5–1444× above baseline).

**What it misses (5/20):** Stealthy, low-volume C2 (e.g., 16 malicious flows among 3,193 benign) sitting at the threshold boundary.

### 3.3 Key Findings

- **Run-to-run variance** exists when threshold is calibrated on small benign sets (~14 devices). Loud attacks are always caught; stealthy always missed — threshold calibration is the variable.
- **PC traffic hurts detection.** Adding general-host captures dropped detection from 75% → 20%. Train on IoT-like traffic only.
- **Per-asset baselining** (each device's early-life behavior as its baseline) is the path to universal device support and stable thresholds.

### 3.4 Honesty Notes

- IoT-23 is lab data, not real home/field traffic. Field validation is pending.
- An earlier benchmark appeared artificially perfect due to a label-parsing bug; corrected numbers are reported above.

---

## 4. Predictive Maintenance — C-MAPSS Evaluation

### 4.1 Approach

Using NASA C-MAPSS turbofan degradation data, the forecaster predicts the next cycle's sensor vector from prior cycles. Trained **only on the first 50% of each engine's life** (assumed healthy). Failure = rising forecast error.

Each engine is normalized by mean/std of its **own first 20 cycles** (per-asset baselining). Near-constant channels are dropped by variance threshold.

### 4.2 Results

| Subset | Op. Conditions | Fault Modes | Error Rise | Detection @1% FPR | Median Lead |
|--------|----------------|-------------|------------|-------------------|-------------|
| FD001 | 1 | 1 | 1.9 → 53.1 (~28×) | **100% (20/20)** | 54 cycles |
| FD003 | 1 | 2 | 2.2 → 91.3 (~41×) | **100% (20/20)** | 60 cycles |
| FD002 | 6 | 1 | non-monotonic | 2% (1/52) | — |
| FD004 | 6 | 2 | non-monotonic | 4% (2/49) | — |

### 4.3 Key Findings

- **Single operating condition = reliable detection.** Error is flat while healthy, rises sharply toward failure.
- **Multiple fault modes are not the problem.** FD003 (two fault modes) works as well as FD001.
- **Multiple operating conditions are the problem.** Regime switches dominate error on FD002/FD004, collapsing detection to 2–4%.
- **Deployable today:** steady, constant-duty rotating equipment (pumps, base-load motors, constant-speed fans).
- **Future work:** regime-aware normalization for variable-duty assets.

---

## 5. Discussion

### 5.1 Why Mamba-2 for Anomaly Detection

Transformers scale memory O(n) with sequence length via KV cache. For long-running device histories, Mamba-2's O(1) recurrent state is a practical advantage on CPU-only edge hardware. Sparse attention supplements local pattern matching without restoring full quadratic cost.

### 5.2 Limitations

- Vigilo: stealthy low-volume C2 remains hard; per-device baselining is on the roadmap.
- PdM: multi-regime equipment (FD002/FD004) requires regime-aware baselines not yet implemented.
- Both evaluations use public lab datasets; real-world field validation is ongoing.

### 5.3 Future Work

- Vigilo per-device in-place baselining
- PdM regime-aware normalization
- Vigilo field validation on home/enterprise networks
- Ensemble scoring improvements for stealthy IoT C2

---

## 6. Conclusion

We demonstrate that a compact hybrid Mamba-2 forecaster (~1.3M parameters) detects meaningful anomalies in both network traffic and industrial sensor data while running entirely on CPU with benign-only training data. Vigilo achieves 75% detection at 1% FPR on IoT-23; the same backbone achieves 100% detection at 1% FPR on single-condition C-MAPSS subsets.

These results define honest operating envelopes: loud IoT attacks and steady-state industrial equipment today; stealthy C2 and variable-duty machinery as targeted next steps.

Vigilo source code: https://github.com/pgalyen1987/Vigilo

---

## References

- Dao & Gu [2024]: "Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality." ICML 2024. arXiv:2405.21060
- Gu & Dao [2023]: "Mamba: Linear-Time Sequence Modeling with Selective State Spaces." arXiv:2312.00752
- Lieber et al. [2024]: "Jamba: A Hybrid Transformer-Mamba Language Model." arXiv:2403.19887
- Glorioso et al. [2024]: "The Zamba2 Suite: Technical Report." arXiv:2411.15242
- Garcia et al. [2020]: "IoT-23: A Labeled Dataset with Malicious and Benign IoT Network Traffic." Stratosphere Laboratory.
- Saxena et al. [2008]: "Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation (C-MAPSS)." PHM 2008.
- Su et al. [2019]: "Robust Anomaly Detection for Multivariate Time Series through Stochastic Recurrent Neural Network (OmniAnomaly)." KDD 2019.
