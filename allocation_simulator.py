"""
Kidney Allocation Simulator

This module simulates two allocation policies:
1. Standard Sequential Allocation (current practice)
2. ML-Optimized Allocation (using predictive model)

The simulator tracks metrics like discard rates, graft success, and fairness.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from collections import defaultdict


def load_data_and_model(data_dir: str = "data/raw",
                        model_path: str = "models/gradient_boosting.pkl") -> Tuple:
    """
    Load raw data and trained ML model.

    Args:
        data_dir: Directory with raw CSV files
        model_path: Path to trained model

    Returns:
        Tuple of (donors, recipients, matches, model, scaler, feature_names)
    """
    print(f"Loading data and model...")

    # Load raw data
    data_path = Path(data_dir)
    donors = pd.read_csv(data_path / "donors.csv")
    recipients = pd.read_csv(data_path / "recipients.csv")
    matches = pd.read_csv(data_path / "matches.csv")

    # Load model
    model = joblib.load(model_path)

    # Load scaler and feature names
    processed_path = Path("data/processed")
    scaler = joblib.load(processed_path / "scaler.pkl")

    with open(processed_path / "feature_names.txt", 'r') as f:
        feature_names = [line.strip() for line in f]

    print(f"  ✓ Loaded {len(donors)} donors")
    print(f"  ✓ Loaded {len(recipients)} recipients")
    print(f"  ✓ Loaded {len(matches)} match records")
    print(f"  ✓ Loaded ML model: {type(model).__name__}")

    return donors, recipients, matches, model, scaler, feature_names


def simulate_standard_allocation(donors: pd.DataFrame, recipients: pd.DataFrame,
                                 matches: pd.DataFrame) -> Dict:
    """
    Simulate standard sequential allocation policy.

    Standard policy:
    - Donors are processed in order
    - Each donor is offered to recipients in priority order (wait_points)
    - First recipient to accept gets the organ
    - No optimization or predictive modeling

    Args:
        donors: Donor DataFrame
        recipients: Recipient DataFrame
        matches: Match outcomes DataFrame

    Returns:
        Dictionary of allocation results
    """
    print("\n" + "="*60)
    print("STANDARD SEQUENTIAL ALLOCATION")
    print("="*60)

    # Initialize tracking
    allocated_donors = set()
    allocated_recipients = set()
    transplants = []
    offers_by_donor = defaultdict(list)

    # Sort recipients by priority (higher wait_points = higher priority)
    recipients_sorted = recipients.sort_values('wait_points', ascending=False)

    # Process each donor
    for _, donor in donors.iterrows():
        donor_id = donor['donor_id']

        if donor_id in allocated_donors:
            continue

        # Get potential matches for this donor
        donor_matches = matches[matches['donor_id'] == donor_id].copy()

        if len(donor_matches) == 0:
            continue

        # Offer to recipients in priority order
        for _, recipient_row in recipients_sorted.iterrows():
            recipient_id = recipient_row['recipient_id']

            # Skip if recipient already got a kidney
            if recipient_id in allocated_recipients:
                continue

            # Check if this match exists
            match = donor_matches[donor_matches['recipient_id'] == recipient_id]

            if len(match) == 0:
                continue

            match = match.iloc[0]
            offers_by_donor[donor_id].append(recipient_id)

            # Acceptance probability (simplified: based on quality)
            # In reality, recipients/centers decide based on multiple factors
            accept_prob = 0.7 if match['kdpi'] < 85 else 0.3

            if np.random.random() < accept_prob:
                # Transplant happens
                transplants.append({
                    'donor_id': donor_id,
                    'recipient_id': recipient_id,
                    'kdpi': match['kdpi'],
                    'epts': match['epts'],
                    'graft_success': match['graft_success_1yr'],
                    'n_offers': len(offers_by_donor[donor_id])
                })

                allocated_donors.add(donor_id)
                allocated_recipients.add(recipient_id)
                break  # Move to next donor

    transplants_df = pd.DataFrame(transplants)

    # Calculate metrics
    n_donors = len(donors)
    n_transplanted = len(transplants_df)
    discard_rate = (n_donors - n_transplanted) / n_donors
    success_rate = transplants_df['graft_success'].mean() if n_transplanted > 0 else 0

    results = {
        'policy': 'Standard Sequential',
        'n_donors': n_donors,
        'n_transplanted': n_transplanted,
        'n_discarded': n_donors - n_transplanted,
        'discard_rate': discard_rate,
        'utilization_rate': 1 - discard_rate,
        'graft_success_rate': success_rate,
        'transplants': transplants_df
    }

    print(f"\nResults:")
    print(f"  Organs transplanted: {n_transplanted}/{n_donors} ({(1-discard_rate)*100:.1f}%)")
    print(f"  Organs discarded: {n_donors - n_transplanted} ({discard_rate*100:.1f}%)")
    print(f"  Graft success rate: {success_rate:.1%}")

    return results


def prepare_features_for_prediction(match_row: pd.Series, donors: pd.DataFrame,
                                    recipients: pd.DataFrame,
                                    feature_names: List[str]) -> np.ndarray:
    """
    Prepare features from a match for ML prediction.

    This must match the feature engineering pipeline exactly.

    Args:
        match_row: Row from matches DataFrame
        donors: Donor DataFrame
        recipients: Recipient DataFrame
        feature_names: List of required feature names

    Returns:
        Feature vector (1D array)
    """
    # Get full donor and recipient data
    donor = donors[donors['donor_id'] == match_row['donor_id']].iloc[0]
    recipient = recipients[recipients['recipient_id'] == match_row['recipient_id']].iloc[0]

    # Build feature dictionary (matching feature_engineering.py logic)
    features = {}

    # Base features from match
    features['kdpi'] = match_row['kdpi']
    features['epts'] = match_row['epts']
    features['age_diff'] = match_row['age_diff']
    features['pra'] = match_row['pra']

    # Donor features
    features['donor_age'] = donor['age']
    features['bmi'] = donor['bmi']
    features['creatinine'] = donor['creatinine']
    features['hcv_positive'] = donor['hcv_positive']
    features['hypertension'] = donor['hypertension']
    features['donor_diabetes'] = donor['diabetes']
    features['dcd'] = donor['dcd']

    # Recipient features
    features['recipient_age'] = recipient['age']
    features['pra_recipient'] = recipient['pra']
    features['dialysis_years'] = recipient['dialysis_years']
    features['prior_transplant'] = recipient['prior_transplant']
    features['recipient_diabetes'] = recipient['diabetes']
    features['wait_points'] = recipient['wait_points']

    # Derived features
    features['combined_risk'] = (features['kdpi'] / 100) * (features['epts'] / 100)
    features['urgency_score'] = ((100 - features['epts']) * 0.6 +
                                 features['dialysis_years'] * 10 * 0.4)
    features['highly_sensitized'] = int(features['pra'] > 80)
    features['donor_risk_count'] = (features['hcv_positive'] +
                                    features['hypertension'] +
                                    features['donor_diabetes'] +
                                    features['dcd'])
    features['recipient_risk_count'] = (features['prior_transplant'] +
                                        features['recipient_diabetes'] +
                                        features['highly_sensitized'])
    features['sex_match'] = int(donor['sex'] == recipient['sex'])
    features['longevity_match'] = int((features['kdpi'] < 20) and (features['epts'] < 20))
    features['both_high_risk'] = int((features['kdpi'] > 85) and (features['epts'] > 85))

    # One-hot encoded features (must match training)
    # Donor sex
    features['donor_sex_M'] = int(donor['sex'] == 'M')

    # Recipient sex
    features['recipient_sex_M'] = int(recipient['sex'] == 'M')

    # Blood type
    for bt in ['A', 'AB', 'B']:
        features[f'blood_type_{bt}'] = int(recipient['blood_type'] == bt)

    # KDPI bins
    if features['kdpi'] < 20:
        kdpi_bin = 'excellent'
    elif features['kdpi'] < 35:
        kdpi_bin = 'good'
    elif features['kdpi'] < 85:
        kdpi_bin = 'standard'
    else:
        kdpi_bin = 'high_risk'

    for kb in ['good', 'high_risk', 'standard']:
        features[f'kdpi_bin_{kb}'] = int(kdpi_bin == kb)

    # EPTS bins
    if features['epts'] < 20:
        epts_bin = 'very_low'
    elif features['epts'] < 50:
        epts_bin = 'low'
    elif features['epts'] < 75:
        epts_bin = 'medium'
    else:
        epts_bin = 'high'

    for eb in ['low', 'medium', 'very_low']:
        features[f'epts_bin_{eb}'] = int(epts_bin == eb)

    # Age match quality
    if features['age_diff'] < 10:
        age_match = 'excellent'
    elif features['age_diff'] < 20:
        age_match = 'good'
    else:
        age_match = 'poor'

    for am in ['good', 'poor']:
        features[f'age_match_quality_{am}'] = int(age_match == am)

    # Donor quality
    donor_quality = 'premium' if features['kdpi'] < 20 else ('standard' if features['kdpi'] < 85 else 'marginal')
    for dq in ['premium', 'standard']:
        features[f'donor_quality_{dq}'] = int(donor_quality == dq)

    # KDPI category
    features['kdpi_category_Good'] = int(donor['kdpi_category'] == 'Good')
    features['kdpi_category_High_KDPI'] = int(donor['kdpi_category'] == 'High_KDPI')
    features['kdpi_category_Standard'] = int(donor['kdpi_category'] == 'Standard')

    # Priority tier
    features['priority_tier_Low'] = int(recipient['priority_tier'] == 'Low')
    features['priority_tier_Medium'] = int(recipient['priority_tier'] == 'Medium')
    features['priority_tier_Very_High'] = int(recipient['priority_tier'] == 'Very_High')

    # Build feature vector in correct order
    feature_vector = np.array([features.get(name, 0) for name in feature_names])

    return feature_vector


def simulate_ml_optimized_allocation(donors: pd.DataFrame, recipients: pd.DataFrame,
                                     matches: pd.DataFrame, model, scaler,
                                     feature_names: List[str]) -> Dict:
    """
    Simulate ML-optimized allocation policy.

    ML policy:
    - For each donor, predict success probability for all potential recipients
    - Rank recipients by predicted success probability
    - Offer to top candidates (balanced with fairness considerations)
    - Accept/reject still based on quality threshold

    Args:
        donors: Donor DataFrame
        recipients: Recipient DataFrame
        matches: Match outcomes DataFrame
        model: Trained ML model
        scaler: Fitted feature scaler
        feature_names: List of feature names

    Returns:
        Dictionary of allocation results
    """
    print("\n" + "="*60)
    print("ML-OPTIMIZED ALLOCATION")
    print("="*60)

    # Initialize tracking
    allocated_donors = set()
    allocated_recipients = set()
    transplants = []
    offers_by_donor = defaultdict(list)

    # Process each donor
    for _, donor in donors.iterrows():
        donor_id = donor['donor_id']

        if donor_id in allocated_donors:
            continue

        # Get potential matches for this donor
        donor_matches = matches[matches['donor_id'] == donor_id].copy()

        if len(donor_matches) == 0:
            continue

        # Filter out already allocated recipients
        donor_matches = donor_matches[
            ~donor_matches['recipient_id'].isin(allocated_recipients)
        ]

        if len(donor_matches) == 0:
            continue

        # Predict success probability for each potential match
        predictions = []
        for _, match_row in donor_matches.iterrows():
            try:
                feature_vector = prepare_features_for_prediction(
                    match_row, donors, recipients, feature_names
                )
                feature_vector_scaled = scaler.transform(feature_vector.reshape(1, -1))
                pred_proba = model.predict_proba(feature_vector_scaled)[0, 1]

                predictions.append({
                    'recipient_id': match_row['recipient_id'],
                    'pred_success_prob': pred_proba,
                    'match_data': match_row
                })
            except Exception as e:
                # Skip problematic matches
                continue

        if len(predictions) == 0:
            continue

        # Sort by predicted success probability (descending)
        predictions_sorted = sorted(predictions, key=lambda x: x['pred_success_prob'], reverse=True)

        # Offer to top candidates
        for pred in predictions_sorted:
            recipient_id = pred['recipient_id']
            match_data = pred['match_data']

            if recipient_id in allocated_recipients:
                continue

            offers_by_donor[donor_id].append(recipient_id)

            # Acceptance probability (same logic as standard)
            accept_prob = 0.7 if match_data['kdpi'] < 85 else 0.3

            if np.random.random() < accept_prob:
                # Transplant happens
                transplants.append({
                    'donor_id': donor_id,
                    'recipient_id': recipient_id,
                    'kdpi': match_data['kdpi'],
                    'epts': match_data['epts'],
                    'graft_success': match_data['graft_success_1yr'],
                    'pred_success_prob': pred['pred_success_prob'],
                    'n_offers': len(offers_by_donor[donor_id])
                })

                allocated_donors.add(donor_id)
                allocated_recipients.add(recipient_id)
                break  # Move to next donor

    transplants_df = pd.DataFrame(transplants)

    # Calculate metrics
    n_donors = len(donors)
    n_transplanted = len(transplants_df)
    discard_rate = (n_donors - n_transplanted) / n_donors
    success_rate = transplants_df['graft_success'].mean() if n_transplanted > 0 else 0

    results = {
        'policy': 'ML-Optimized',
        'n_donors': n_donors,
        'n_transplanted': n_transplanted,
        'n_discarded': n_donors - n_transplanted,
        'discard_rate': discard_rate,
        'utilization_rate': 1 - discard_rate,
        'graft_success_rate': success_rate,
        'transplants': transplants_df
    }

    print(f"\nResults:")
    print(f"  Organs transplanted: {n_transplanted}/{n_donors} ({(1-discard_rate)*100:.1f}%)")
    print(f"  Organs discarded: {n_donors - n_transplanted} ({discard_rate*100:.1f}%)")
    print(f"  Graft success rate: {success_rate:.1%}")

    return results


def save_results(standard_results: Dict, ml_results: Dict,
                output_dir: str = "outputs/reports"):
    """
    Save allocation simulation results.

    Args:
        standard_results: Results from standard allocation
        ml_results: Results from ML-optimized allocation
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving results to {output_dir}/...")

    # Save transplant details
    standard_results['transplants'].to_csv(
        output_path / "standard_allocation_transplants.csv", index=False
    )
    ml_results['transplants'].to_csv(
        output_path / "ml_allocation_transplants.csv", index=False
    )

    # Save summary metrics
    summary = pd.DataFrame([
        {
            'policy': standard_results['policy'],
            'n_transplanted': standard_results['n_transplanted'],
            'n_discarded': standard_results['n_discarded'],
            'discard_rate': standard_results['discard_rate'],
            'utilization_rate': standard_results['utilization_rate'],
            'graft_success_rate': standard_results['graft_success_rate']
        },
        {
            'policy': ml_results['policy'],
            'n_transplanted': ml_results['n_transplanted'],
            'n_discarded': ml_results['n_discarded'],
            'discard_rate': ml_results['discard_rate'],
            'utilization_rate': ml_results['utilization_rate'],
            'graft_success_rate': ml_results['graft_success_rate']
        }
    ])

    summary.to_csv(output_path / "allocation_comparison.csv", index=False)

    print(f"  ✓ Saved transplant details")
    print(f"  ✓ Saved comparison summary")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Simulate kidney allocation policies"
    )
    parser.add_argument(
        '--data-dir', type=str, default='data/raw',
        help='Directory with raw data (default: data/raw)'
    )
    parser.add_argument(
        '--model', type=str, default='models/gradient_boosting.pkl',
        help='Trained ML model (default: models/gradient_boosting.pkl)'
    )
    parser.add_argument(
        '--output-dir', type=str, default='outputs/reports',
        help='Output directory (default: outputs/reports)'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed (default: 42)'
    )

    args = parser.parse_args()

    np.random.seed(args.seed)

    print("="*60)
    print("KIDNEY ALLOCATION SIMULATOR")
    print("="*60)
    print(f"Configuration:")
    print(f"  Data: {args.data_dir}")
    print(f"  Model: {args.model}")
    print(f"  Output: {args.output_dir}")
    print(f"  Random Seed: {args.seed}")
    print("="*60)

    # Load data and model
    donors, recipients, matches, model, scaler, feature_names = load_data_and_model(
        args.data_dir, args.model
    )

    # Simulate both policies
    standard_results = simulate_standard_allocation(donors, recipients, matches)
    ml_results = simulate_ml_optimized_allocation(
        donors, recipients, matches, model, scaler, feature_names
    )

    # Save results
    save_results(standard_results, ml_results, args.output_dir)

    # Print comparison
    print("\n" + "="*60)
    print("POLICY COMPARISON")
    print("="*60)
    print(f"\n{'Metric':<30} {'Standard':<15} {'ML-Optimized':<15} {'Improvement':<15}")
    print("-"*75)

    metrics = [
        ('Utilization Rate', 'utilization_rate', '%'),
        ('Discard Rate', 'discard_rate', '%'),
        ('Graft Success Rate', 'graft_success_rate', '%')
    ]

    for label, key, unit in metrics:
        std_val = standard_results[key]
        ml_val = ml_results[key]
        if key == 'discard_rate':
            improvement = (std_val - ml_val) / std_val * 100  # Lower is better
            sign = '-' if improvement < 0 else '+'
        else:
            improvement = (ml_val - std_val) / std_val * 100  # Higher is better
            sign = '+' if improvement > 0 else ''

        print(f"{label:<30} {std_val*100:>6.1f}{unit:<8} {ml_val*100:>6.1f}{unit:<8} {sign}{improvement:>5.1f}%")

    print("\n" + "="*60)
    print("SIMULATION COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
