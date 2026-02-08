# Kidney Allocation Optimization System

## Overview

This project implements a machine learning-based kidney allocation simulation system that compares traditional sequential allocation policies with ML-optimized allocation strategies. The goal is to reduce organ discard rates while maintaining fairness and optimizing transplant outcomes.

## Project Structure

```
BioHack/
├── data/
│   ├── raw/                  # Raw synthetic data
│   └── processed/            # Processed features
├── models/                   # Trained ML models
├── outputs/
│   ├── plots/               # Visualization outputs
│   └── reports/             # Evaluation reports
├── data_generator.py        # Synthetic data generation
├── feature_engineering.py   # Feature processing pipeline
├── model_training.py        # ML model training
├── allocation_simulator.py  # Allocation policy simulation
├── evaluation.py            # Performance evaluation
├── main.py                  # Main pipeline orchestrator
├── requirements.txt         # Project dependencies
└── README.md               # This file
```

## Medical Context

### KDPI (Kidney Donor Profile Index)
- A composite metric (0-100%) assessing donor kidney quality
- Higher KDPI = lower quality organs
- KDPI > 85% often face high discard rates (~60%)

### EPTS (Estimated Post-Transplant Survival)
- Metric for recipient priority (0-100%)
- Lower EPTS = higher priority (longer expected survival)

### Current Challenge
Standard sequential allocation leads to:
- High discard rates for marginal organs (KDPI > 85%)
- Inefficient matching of donors to recipients
- Potential life-saving transplants never happening

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Full Pipeline
```bash
python main.py --n-donors 5000 --n-recipients 3000
```

### Individual Components

**1. Generate Synthetic Data**
```bash
python data_generator.py --n-donors 5000 --n-recipients 3000
```

**2. Engineer Features**
```bash
python feature_engineering.py
```

**3. Train Models**
```bash
python model_training.py
```

**4. Run Allocation Simulation**
```bash
python allocation_simulator.py
```

**5. Generate Evaluation Report**
```bash
python evaluation.py
```

## Key Metrics

- **Discard Rate**: Percentage of organs not transplanted
- **Graft Success Rate**: Percentage of successful transplants
- **Utilization Rate**: Percentage of organs used
- **Fairness Metrics**: Distribution across priority groups

## Expected Outcomes

The ML-optimized allocation should demonstrate:
- 15-30% reduction in organ discard rates
- Maintained or improved graft success rates
- Fair distribution across recipient priority tiers
- Better utilization of marginal quality organs

## Future Enhancements

1. Incorporate real OPTN/UNOS data (with appropriate permissions)
2. Add geographic constraints and logistics
3. Implement dynamic waitlist updates
4. Include HLA compatibility matching
5. Add temporal dynamics (organ aging, recipient health changes)
6. Multi-objective optimization (fairness + efficiency + outcomes)

## Medical Disclaimer

This is a research simulation tool using synthetic data. It is NOT intended for clinical decision-making. Real kidney allocation policies are governed by OPTN/UNOS and involve complex medical, ethical, and regulatory considerations.

## License

Educational and research purposes only.

## Author

BioHack Project
