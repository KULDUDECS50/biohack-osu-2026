# KIDNEY ALLOCATION OPTIMIZATION SYSTEM - IMPLEMENTATION GUIDE
# =============================================================================

## 🎯 PROJECT OVERVIEW

**Goal**: Build a machine learning-based kidney allocation simulation system that compares traditional sequential allocation policies with ML-optimized strategies to reduce organ discard rates while maintaining fairness.

**Key Success Metrics:**
- Reduce organ discard rate by 15-30% (especially KDPI > 85%)
- Maintain or improve graft success rates (target: >85%)
- Preserve fairness across priority groups
- Demonstrate better utilization of marginal organs

**Medical Context:**
- **KDPI (Kidney Donor Profile Index)**: 0-100% score, higher = lower quality
- **EPTS (Estimated Post-Transplant Survival)**: 0-100% recipient priority, lower = higher priority
- **Current Challenge**: ~60% of high KDPI organs (>85%) are discarded under current policies

---

## 📋 PRE-IMPLEMENTATION CHECKLIST

Before starting implementation:
- [ ] Python 3.8+ installed
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Understand medical domain (KDPI, EPTS, allocation policies)
- [ ] Clear project directory structure planned
- [ ] Git repository initialized (optional but recommended)

---

## 🏗️ IMPLEMENTATION ORDER

### STEP 1: Project Setup ⚙️
**Time estimate: 15 minutes**

**Tasks:**
1. Create directory structure:
   ```
   BioHack/
   ├── data/raw/          # Raw synthetic data
   ├── data/processed/    # Processed features
   ├── models/            # Trained ML models
   ├── outputs/plots/     # Visualizations
   └── outputs/reports/   # Evaluation reports
   ```

2. Write `requirements.txt` with core dependencies:
   - pandas, numpy (data manipulation)
   - scikit-learn (ML models)
   - matplotlib, seaborn (visualization)
   - joblib (model persistence)

3. Create `README.md` with:
   - Project overview and medical context
   - Installation instructions
   - Usage examples
   - Key metrics definitions
   - Medical disclaimer

**Validation:**
- [ ] All directories created
- [ ] Can install dependencies: `pip install -r requirements.txt`
- [ ] README is comprehensive and clear

---

### STEP 2: Data Generation (data_generator.py) 🧬
**Time estimate: 2-3 hours**

**Medical Realism Requirements:**

**Donor Generation:**
- KDPI distribution: Right-skewed (more low KDPI = high quality)
  - Excellent (0-20%): ~30%
  - Good (20-35%): ~35-40%
  - Standard (35-85%): ~25-30%
  - High risk (85-100%): ~5-10%
- Age distribution: Bimodal (young trauma victims 20-35, older donors 45-70)
- Comorbidities correlated with age:
  - HCV: Rare (<5%)
  - Hypertension: 30-50% in older donors
  - Diabetes: 10-20% in older donors
- DCD vs DBD classification

**Recipient Generation:**
- EPTS calculation: Based on age, diabetes, prior transplant, dialysis time
- Priority tiers: Very High (<20), High (20-50), Medium (50-80), Low (>80)
- Wait list points: Higher for longer wait times
- PRA (sensitization): Most 0%, some 20-80% (harder to match)

**Outcome Labeling:**
- Base graft success: ~85%
- Penalties:
  - High KDPI: -10% to -20%
  - Poor age matching: -5% to -10%
  - High PRA: -5%
  - Multiple comorbidities: -5% each
- Realistic success rate range: 50-95%

**Data Validation Checks:**
1. No missing values
2. KDPI in [0, 100]
3. EPTS in [0, 100]
4. Ages realistic (18-80 donors, 18-75 recipients)
5. Referential integrity (match IDs valid)
6. Reasonable success rate distribution (60-80% overall)

**Code Requirements:**
- Type hints for all functions
- Docstrings with parameter descriptions
- Progress indicators for large datasets
- Save as CSV files (donors.csv, recipients.csv, matches.csv)
- CLI arguments: `--n-donors`, `--n-recipients`, `--seed`

**Expected Output:**
```
Generated 1000 donors (KDPI: Excellent: 296, Good: 410, ...)
Generated 600 recipients (Priority: Very_High: 78, High: 403, ...)
Generated 7549 potential matches (69.0% success rate)
✓ All validation checks passed!
Saved to data/raw/
```

**Testing:**
```bash
python data_generator.py --n-donors 1000 --n-recipients 600
# Check: data/raw/ contains 3 CSV files
# Validate: Success rate between 65-75%
```

---

### STEP 3: Feature Engineering (feature_engineering.py) 🔧
**Time estimate: 1-2 hours**

**Derived Features to Create:**

**Categorical Bins:**
- KDPI bins: excellent (0-20), good (20-35), standard (35-85), high_risk (85-100)
- EPTS bins: very_low (0-20), low (20-50), medium (50-80), high (80-100)
- Age matching quality: excellent (<5yr diff), good (5-10yr), poor (>10yr)

**Risk Scores:**
- Combined risk: KDPI × EPTS / 10000 (interaction term)
- Urgency score: (100 - EPTS) + dialysis_time / 365
- Donor risk count: sum(HCV, hypertension, diabetes, DCD)
- Recipient risk count: sum(diabetes, high_PRA)

**Compatibility Features:**
- Age difference (absolute)
- Sex matching (binary)
- Sensitization flags (PRA > 50, PRA > 80)
- High-risk pairing detection

**Encoding:**
- One-hot encoding for nominal categories
- Keep ordinal features as numeric
- Drop first category to avoid multicollinearity

**Data Splitting:**
- 80/20 train-test split
- Stratify by outcome (maintain success rate balance)
- StandardScaler for feature normalization
- Save scaler for inference

**Code Requirements:**
- Load from data/raw/, save to data/processed/
- Save as .npy arrays for efficiency
- Save feature_names.pkl for interpretability
- Print feature count and sample distributions

**Expected Output:**
```
Total features: 44 (after encoding)
Training: 6039 samples (69.0% success)
Test: 1510 samples (69.1% success)
Saved to data/processed/
```

**Testing:**
```bash
python feature_engineering.py
# Verify: data/processed/ contains X_train.npy, y_train.npy, etc.
# Check: Feature means ≈ 0, stds ≈ 1 after scaling
```

---

### STEP 4: ML Model Training (model_training.py) 🤖
**Time estimate: 2-3 hours**

**Models to Train:**

1. **Logistic Regression** (baseline)
   - Fast, interpretable
   - Expected: 0.55-0.60 accuracy

2. **Random Forest**
   - Handles non-linear relationships
   - Feature importance built-in
   - Expected: 0.60-0.70 accuracy

3. **Gradient Boosting** (typically best)
   - Best performance on tabular data
   - Well-calibrated probabilities
   - Expected: 0.65-0.75 accuracy

**Training Protocol:**
- 5-fold stratified cross-validation
- Track: Accuracy, F1, ROC AUC, Precision, Recall
- Calibration checking (ECE: Expected Calibration Error)
- Feature importance for tree models

**Evaluation Metrics:**
- **Accuracy**: Overall correct predictions
- **F1 Score**: Balance of precision/recall (important for imbalanced data)
- **ROC AUC**: Ranking quality
- **Calibration**: Predicted probabilities match actual rates

**Visualizations to Generate:**
1. ROC curves (all 3 models compared)
2. Calibration plots (reliability diagrams)
3. Feature importance (top 20 features)
4. Confusion matrices

**Model Selection:**
- Choose model with best F1 score and calibration
- Gradient Boosting typically wins
- Save best model as `gradient_boosting.pkl`

**Code Requirements:**
- Cross-validation for robust evaluation
- Save all 3 models for comparison
- Generate plots in outputs/plots/
- Print comparison table

**Expected Output:**
```
Logistic Regression: Acc=0.583, F1=0.672, AUC=0.584
Random Forest:       Acc=0.625, F1=0.735, AUC=0.575
Gradient Boosting:   Acc=0.673, F1=0.797, AUC=0.571 ⭐

Top features: age_diff, combined_risk, kdpi, bmi, donor_age
Saved models to models/
```

**Testing:**
```bash
python model_training.py
# Verify: 3 .pkl files in models/
# Check: F1 score > 0.70 for best model
```

---

### STEP 5: Allocation Simulator (allocation_simulator.py) 🏥
**Time estimate: 2-3 hours**

**Policy 1: Standard Sequential Allocation**
```
For each donor (in order):
  Get eligible recipients (compatible)
  Sort by priority (wait_points descending)
  Offer to #1 recipient
  If accepted → transplant
  If rejected → offer to #2
  If all reject → discard organ
```

**Policy 2: ML-Optimized Allocation**
```
For each donor:
  Get eligible recipients
  Predict success probability for all (ML model)
  Rank by predicted success
  Offer to top candidates
  Track outcomes
```

**Acceptance Logic:**
- Standard: Accept if wait_points > threshold (priority-based)
- ML: Accept if predicted_success > 0.5 (outcome-based)

**Metrics to Track:**
- Utilization rate (% organs transplanted)
- Discard rate (% organs discarded)
- Graft success rate (% successful transplants)
- Distribution by priority tier (fairness)
- Distribution by KDPI category

**Simulation Requirements:**
- Run on test set only (no data leakage)
- Track every offer, acceptance, rejection
- Save detailed results for analysis
- Compare both policies side-by-side

**Code Requirements:**
- Load model: `--model models/gradient_boosting.pkl`
- Save transplant logs: CSV with donor, recipient, outcome
- Print summary comparison table

**Expected Output:**
```
STANDARD SEQUENTIAL:
  Utilization: 59.8%
  Discard Rate: 40.2%
  Graft Success: 67.6%

ML-OPTIMIZED:
  Utilization: 59.6% (-0.3%)
  Discard Rate: 40.4% (+0.5%)
  Graft Success: 82.0% (+21.4%) ⭐

Key Insight: ML significantly improves outcomes without reducing utilization
```

**Testing:**
```bash
python allocation_simulator.py --model models/gradient_boosting.pkl
# Verify: outputs/reports/ contains allocation CSVs
# Check: ML success rate > Standard success rate
```

---

### STEP 6: Evaluation & Visualization (evaluation.py) 📊
**Time estimate: 2-3 hours**

**Visualizations to Generate:**

1. **Policy Comparison Summary** (bar charts)
   - Utilization rates side-by-side
   - Graft success rates side-by-side
   - Clear percentage improvements labeled

2. **Discard Rates by KDPI Category**
   - 4 KDPI bins: 0-20, 20-35, 35-85, 85-100
   - Compare Standard vs ML
   - Highlight: ML should improve high-KDPI utilization

3. **Outcomes by Priority Tier**
   - Graft success for each tier (Very High, High, Medium, Low)
   - Compare Standard vs ML
   - Verify: ML improves all tiers (fairness preserved)

4. **KDPI × EPTS Heatmap**
   - 2D grid showing success rates
   - Identify: Which combinations benefit most from ML

5. **Fairness Metrics Table**
   - % transplants by priority tier (should be similar)
   - Success rates by tier (ML should improve all)

**Statistical Analysis:**
- Chi-square test for distribution fairness
- T-test for outcome improvements
- Effect sizes for clinical significance

**Report Generation:**
- `evaluation_report.txt`: Comprehensive summary
- `allocation_comparison.csv`: Detailed metrics
- `fairness_metrics.csv`: Priority tier breakdown

**Code Requirements:**
- High-quality matplotlib plots (publication-ready)
- Clear labels, legends, titles
- Save all plots as PNG (300 DPI)
- Generate human-readable text report

**Expected Output:**
```
Generated 10 visualizations:
  ✓ policy_comparison_summary.png
  ✓ discard_by_kdpi.png
  ✓ outcomes_by_priority.png
  ✓ kdpi_epts_heatmap.png
  ✓ fairness_analysis.png
  ... (ROC curves, calibration, feature importance)

Key Findings:
  • 21.4% improvement in graft success
  • Fairness maintained across all priority tiers
  • ML excels at matching marginal organs
```

**Testing:**
```bash
python evaluation.py
# Verify: 8-10 plots in outputs/plots/
# Check: Plots are clear and professional
```

---

### STEP 7: Main Pipeline (main.py) 🚀
**Time estimate: 1-2 hours**

**Orchestration Requirements:**

1. **Sequential Execution:**
   ```
   Step 1: Data Generation
   Step 2: Feature Engineering
   Step 3: Model Training
   Step 4: Allocation Simulation
   Step 5: Evaluation & Visualization
   ```

2. **CLI Arguments:**
   - `--n-donors`: Number of donors (default: 1000)
   - `--n-recipients`: Number of recipients (default: 600)
   - `--seed`: Random seed (default: 42)
   - `--model`: Model path (default: models/gradient_boosting.pkl)
   - `--skip-data-gen`: Skip if data exists
   - `--skip-training`: Skip if models exist
   - `--steps`: Run specific steps only (e.g., "simulate evaluate")

3. **Error Handling:**
   - Check if dependencies installed
   - Verify input files exist
   - Catch and report errors gracefully
   - Provide helpful error messages

4. **Progress Tracking:**
   - Print step headers
   - Show timing for each step
   - Display total execution time
   - List generated outputs

**Code Requirements:**
- Use subprocess to call individual scripts
- OR import and call main functions
- Comprehensive logging
- Clear success/failure indicators

**Expected Output:**
```
============================================
KIDNEY ALLOCATION OPTIMIZATION PIPELINE
============================================
Step 1/5: Data Generation... ✓ (8.2s)
Step 2/5: Feature Engineering... ✓ (2.1s)
Step 3/5: Model Training... ✓ (13.4s)
Step 4/5: Allocation Simulation... ✓ (2.3s)
Step 5/5: Evaluation... ✓ (2.7s)
============================================
COMPLETE! Total time: 28.7s

Generated outputs:
  • Data: data/raw/ (3 files)
  • Models: models/ (3 files)
  • Plots: outputs/plots/ (10 files)
  • Reports: outputs/reports/ (3 files)

Next steps:
  1. Review: outputs/reports/evaluation_report.txt
  2. Visualizations: outputs/plots/
  3. Run with larger dataset: --n-donors 10000
```

**Testing:**
```bash
# Full pipeline
python main.py --n-donors 1000 --n-recipients 600

# Quick test
python main.py --n-donors 100 --n-recipients 60

# Resume from simulation
python main.py --skip-data-gen --skip-training
```

---

## ✅ QUALITY CHECKLIST

### Code Quality:
- [ ] All functions have docstrings with type hints
- [ ] Inline comments explain medical domain logic
- [ ] No hardcoded paths (use pathlib)
- [ ] Progress indicators for long operations
- [ ] Validation checks at each step
- [ ] Error handling with informative messages
- [ ] Reproducible (random seeds set)

### Medical Validity:
- [ ] KDPI/EPTS distributions realistic
- [ ] Outcome probabilities medically plausible
- [ ] Fairness metrics properly defined
- [ ] Medical terminology used correctly
- [ ] Disclaimer about synthetic data included

### ML Best Practices:
- [ ] Proper train/test split (no leakage)
- [ ] Cross-validation for model selection
- [ ] Calibration checking
- [ ] Feature scaling applied
- [ ] Models saved for reproducibility

### Outputs:
- [ ] All visualizations publication-ready
- [ ] Reports comprehensive and clear
- [ ] Results reproducible
- [ ] Key findings highlighted

---

## 🎯 SUCCESS CRITERIA

**Technical:**
✅ All 7 steps implemented and tested
✅ Pipeline runs end-to-end without errors
✅ Code is modular, documented, and maintainable
✅ All outputs generated successfully

**Scientific:**
✅ ML model achieves F1 > 0.70
✅ Graft success improvement > 15%
✅ Fairness maintained across priority groups
✅ Results are medically plausible

**Usability:**
✅ Clear documentation in README
✅ Simple CLI interface
✅ Fast execution (<5 min for 1000 donors)
✅ Easy to extend and modify

---

## 🐛 TROUBLESHOOTING

**Common Issues:**

1. **ImportError**: Missing dependencies
   → `pip install -r requirements.txt`

2. **FileNotFoundError**: Missing data
   → Run `python data_generator.py` first

3. **Low model performance** (F1 < 0.60)
   → Check feature engineering
   → Verify data quality
   → Try different model hyperparameters

4. **Memory issues** with large datasets
   → Process in batches
   → Use smaller test dataset first
   → Check available RAM

5. **Plots not showing**
   → Check matplotlib backend
   → Verify outputs/plots/ directory exists
   → Check file permissions

---

## 🚀 GETTING STARTED

**Quick Start:**
```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Run full pipeline
python main.py --n-donors 1000 --n-recipients 600

# 3. Review results
cat outputs/reports/evaluation_report.txt
ls outputs/plots/
```

**Development Mode:**
```bash
# Test individual components
python data_generator.py --n-donors 100 --n-recipients 60
python feature_engineering.py
python model_training.py
```

---

## 📚 ADDITIONAL RESOURCES

**Medical Context:**
- OPTN/UNOS allocation policies
- KDPI calculator: https://optn.transplant.hrsa.gov/
- Transplant research papers on ML applications

**ML Resources:**
- Scikit-learn documentation
- Calibration in ML: https://scikit-learn.org/stable/modules/calibration.html
- Fairness in ML allocation systems

---

## ⚠️ IMPORTANT NOTES

1. **Medical Disclaimer**: This is a research simulation using synthetic data. NOT for clinical use.

2. **Data Privacy**: All data is synthetically generated. No real patient data used.

3. **Fairness**: Ensure ML doesn't introduce bias. Monitor priority tier distributions.

4. **Validation**: Always validate on held-out test set. No data leakage.

5. **Reproducibility**: Set random seeds for consistent results.

---

**NOW BEGIN IMPLEMENTATION!** Start with Step 1 (Project Setup) and proceed sequentially. Test each component before moving to the next. Good luck! 🎉

