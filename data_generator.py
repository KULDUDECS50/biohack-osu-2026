"""
Synthetic Kidney Allocation Data Generator

This module generates realistic synthetic data for kidney transplant allocation,
including donor characteristics (with KDPI scoring) and recipient characteristics
(with EPTS scoring). The data reflects real-world distributions and medical logic.

Medical Context:
- KDPI (Kidney Donor Profile Index): 0-100%, higher = lower quality
- EPTS (Estimated Post-Transplant Survival): 0-100%, lower = higher priority
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict
import argparse
from pathlib import Path


def calculate_kdpi(age: float, height: float, weight: float,
                   creatinine: float, hcv: int, hypertension: int,
                   diabetes: int, dcd: int) -> float:
    """
    Calculate KDPI score based on donor characteristics.

    This is a simplified version of the actual KDPI formula used by OPTN.
    Real KDPI uses a more complex regression model with additional factors.

    Args:
        age: Donor age in years
        height: Donor height in cm
        weight: Donor weight in kg
        creatinine: Serum creatinine (mg/dL)
        hcv: Hepatitis C status (0=negative, 1=positive)
        hypertension: History of hypertension (0/1)
        diabetes: History of diabetes (0/1)
        dcd: Donation after cardiac death (0=DBD, 1=DCD)

    Returns:
        KDPI score (0-100)
    """
    # Simplified KDPI calculation (normalized to 0-100 scale)
    base_score = 0.0

    # Age is the strongest predictor (scaled to 0-40 points)
    base_score += (age - 18) / (80 - 18) * 40

    # Creatinine (scaled to 0-20 points)
    base_score += min(creatinine / 5.0, 1.0) * 20

    # Comorbidities (5 points each)
    base_score += (hcv + hypertension + diabetes) * 5

    # DCD vs DBD (10 points)
    base_score += dcd * 10

    # BMI component (scaled to 0-10 points)
    bmi = weight / ((height / 100) ** 2)
    bmi_score = 0
    if bmi < 18.5:
        bmi_score = 5  # Underweight
    elif bmi > 35:
        bmi_score = 10  # Severely obese
    elif bmi > 30:
        bmi_score = 5  # Obese
    base_score += bmi_score

    # Normalize to 0-100 range
    kdpi = np.clip(base_score, 0, 100)

    return kdpi


def calculate_epts(age: float, diabetes: int, prior_transplant: int,
                   dialysis_time: float) -> float:
    """
    Calculate EPTS (Estimated Post-Transplant Survival) score.

    Lower EPTS = higher priority/better expected outcomes.

    Args:
        age: Recipient age in years
        diabetes: Diabetes diagnosis (0/1)
        prior_transplant: Previous transplant (0/1)
        dialysis_time: Years on dialysis

    Returns:
        EPTS score (0-100)
    """
    base_score = 0.0

    # Age is primary factor (0-40 points)
    base_score += (age - 18) / (80 - 18) * 40

    # Dialysis time (0-30 points)
    base_score += min(dialysis_time / 10.0, 1.0) * 30

    # Prior transplant (15 points)
    base_score += prior_transplant * 15

    # Diabetes (15 points)
    base_score += diabetes * 15

    # Normalize to 0-100
    epts = np.clip(base_score, 0, 100)

    return epts


def generate_donors(n_donors: int, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic donor data with realistic distributions.

    Distribution characteristics:
    - Age: Bimodal (young donors + older donors)
    - KDPI: Right-skewed (more low KDPI, fewer high KDPI)
    - Comorbidities: Age-correlated

    Args:
        n_donors: Number of donors to generate
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame with donor characteristics and KDPI scores
    """
    np.random.seed(random_seed)

    print(f"Generating {n_donors} synthetic donors...")

    # Age: Bimodal distribution (peaks around 25 and 55)
    age_mode = np.random.choice(['young', 'older'], n_donors, p=[0.3, 0.7])
    age = np.where(
        age_mode == 'young',
        np.random.normal(28, 8, n_donors),
        np.random.normal(52, 12, n_donors)
    )
    age = np.clip(age, 18, 80)

    # Height (cm): Normal distribution by sex
    sex = np.random.choice(['M', 'F'], n_donors, p=[0.55, 0.45])
    height = np.where(
        sex == 'M',
        np.random.normal(175, 10, n_donors),
        np.random.normal(162, 9, n_donors)
    )
    height = np.clip(height, 145, 200)

    # Weight (kg): Correlated with height, some obesity
    bmi_base = np.random.normal(26, 5, n_donors)  # Slightly overweight average
    weight = bmi_base * ((height / 100) ** 2)
    weight = np.clip(weight, 45, 150)

    # Creatinine (mg/dL): Higher in older donors
    creatinine = np.random.gamma(2, 0.4, n_donors) + (age - 40) / 100
    creatinine = np.clip(creatinine, 0.5, 5.0)

    # Comorbidities (age-correlated)
    age_risk = (age - 18) / (80 - 18)  # Normalized age
    hcv = (np.random.random(n_donors) < (0.02 + age_risk * 0.05)).astype(int)
    hypertension = (np.random.random(n_donors) < (0.1 + age_risk * 0.4)).astype(int)
    diabetes = (np.random.random(n_donors) < (0.05 + age_risk * 0.2)).astype(int)

    # DCD vs DBD (Donation after Cardiac Death vs Brain Death)
    dcd = np.random.choice([0, 1], n_donors, p=[0.75, 0.25])

    # Calculate KDPI for each donor
    kdpi_scores = np.array([
        calculate_kdpi(age[i], height[i], weight[i], creatinine[i],
                      hcv[i], hypertension[i], diabetes[i], dcd[i])
        for i in range(n_donors)
    ])

    # Categorize KDPI
    kdpi_category = pd.cut(
        kdpi_scores,
        bins=[0, 20, 35, 85, 100],
        labels=['Excellent', 'Good', 'Standard', 'High_KDPI']
    )

    donors = pd.DataFrame({
        'donor_id': [f'D{i:05d}' for i in range(n_donors)],
        'age': age.round(1),
        'sex': sex,
        'height_cm': height.round(1),
        'weight_kg': weight.round(1),
        'bmi': (weight / ((height / 100) ** 2)).round(1),
        'creatinine': creatinine.round(2),
        'hcv_positive': hcv,
        'hypertension': hypertension,
        'diabetes': diabetes,
        'dcd': dcd,
        'kdpi': kdpi_scores.round(1),
        'kdpi_category': kdpi_category
    })

    print(f"✓ Generated {n_donors} donors")
    print(f"  KDPI distribution: {donors['kdpi_category'].value_counts().to_dict()}")

    return donors


def generate_recipients(n_recipients: int, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic recipient data with priority scoring.

    Distribution characteristics:
    - Age: Broad distribution (ESRD affects all ages)
    - Wait time: Exponential (some wait much longer)
    - EPTS: Correlated with age and comorbidities

    Args:
        n_recipients: Number of recipients to generate
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame with recipient characteristics and EPTS scores
    """
    np.random.seed(random_seed + 1)  # Different seed than donors

    print(f"Generating {n_recipients} synthetic recipients...")

    # Age: Broader distribution than donors
    age = np.random.normal(50, 15, n_recipients)
    age = np.clip(age, 18, 80)

    # Sex
    sex = np.random.choice(['M', 'F'], n_recipients, p=[0.58, 0.42])

    # Blood type (for future compatibility matching)
    blood_type = np.random.choice(['O', 'A', 'B', 'AB'], n_recipients,
                                  p=[0.45, 0.40, 0.11, 0.04])

    # PRA (Panel Reactive Antibody) - sensitization level
    # Higher PRA = harder to match
    pra = np.random.gamma(1.5, 15, n_recipients)
    pra = np.clip(pra, 0, 100)

    # Time on dialysis (years): Exponential-ish distribution
    dialysis_time = np.random.exponential(3, n_recipients)
    dialysis_time = np.clip(dialysis_time, 0.1, 15)

    # Prior transplant (correlated with dialysis time)
    prior_transplant = (np.random.random(n_recipients) <
                       np.clip(dialysis_time / 20, 0, 0.3)).astype(int)

    # Comorbidities
    age_risk = (age - 18) / (80 - 18)
    diabetes = (np.random.random(n_recipients) < (0.3 + age_risk * 0.2)).astype(int)

    # Calculate EPTS for each recipient
    epts_scores = np.array([
        calculate_epts(age[i], diabetes[i], prior_transplant[i], dialysis_time[i])
        for i in range(n_recipients)
    ])

    # Priority tier (lower EPTS = higher priority)
    priority_tier = pd.cut(
        epts_scores,
        bins=[0, 20, 50, 75, 100],
        labels=['Very_High', 'High', 'Medium', 'Low']
    )

    # Wait list points (inverse of EPTS + time bonus)
    wait_points = 100 - epts_scores + dialysis_time * 2

    recipients = pd.DataFrame({
        'recipient_id': [f'R{i:05d}' for i in range(n_recipients)],
        'age': age.round(1),
        'sex': sex,
        'blood_type': blood_type,
        'pra': pra.round(1),
        'dialysis_years': dialysis_time.round(1),
        'prior_transplant': prior_transplant,
        'diabetes': diabetes,
        'epts': epts_scores.round(1),
        'priority_tier': priority_tier,
        'wait_points': wait_points.round(1)
    })

    print(f"✓ Generated {n_recipients} recipients")
    print(f"  Priority distribution: {recipients['priority_tier'].value_counts().to_dict()}")

    return recipients


def label_outcomes(donors: pd.DataFrame, recipients: pd.DataFrame,
                   random_seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic match outcomes based on donor-recipient compatibility.

    Outcome logic:
    - Better outcomes when KDPI is low and EPTS is low (good organ + healthy recipient)
    - Worse outcomes when KDPI is high and EPTS is high (marginal organ + sick recipient)
    - Age matching matters (young organ to young recipient)

    Args:
        donors: Donor DataFrame
        recipients: Recipient DataFrame
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame with match combinations and outcomes
    """
    np.random.seed(random_seed + 2)

    print(f"Generating match outcome labels...")

    # Create a sample of potential matches (not all combinations)
    # Typically 5-10 offers per donor
    matches = []

    for _, donor in donors.iterrows():
        # Each donor gets offered to 5-10 recipients
        n_offers = np.random.randint(5, 11)
        offered_recipients = recipients.sample(n=min(n_offers, len(recipients)))

        for _, recipient in offered_recipients.iterrows():
            # Calculate compatibility score (0-1, higher is better)
            kdpi = donor['kdpi']
            epts = recipient['epts']
            age_diff = abs(donor['age'] - recipient['age'])

            # Base success probability
            # Good outcome more likely with: low KDPI, low EPTS, similar age
            success_prob = 0.85  # Base success rate

            # KDPI penalty (high KDPI reduces success)
            success_prob -= (kdpi / 100) * 0.25

            # EPTS penalty (high EPTS reduces success)
            success_prob -= (epts / 100) * 0.15

            # Age matching bonus
            if age_diff > 30:
                success_prob -= 0.10
            elif age_diff < 10:
                success_prob += 0.05

            # PRA penalty (sensitization makes matching harder)
            success_prob -= (recipient['pra'] / 100) * 0.10

            # Prior transplant penalty
            if recipient['prior_transplant']:
                success_prob -= 0.08

            # Ensure probability bounds
            success_prob = np.clip(success_prob, 0.1, 0.95)

            # Generate outcome
            graft_success = np.random.random() < success_prob

            # Estimated graft survival (1-year)
            if graft_success:
                survival_months = np.random.normal(
                    11 + success_prob * 6,  # Higher prob = longer survival
                    2
                )
            else:
                survival_months = np.random.uniform(0.5, 6)

            matches.append({
                'donor_id': donor['donor_id'],
                'recipient_id': recipient['recipient_id'],
                'kdpi': kdpi,
                'epts': epts,
                'age_diff': age_diff,
                'pra': recipient['pra'],
                'compatibility_score': success_prob * 100,
                'graft_success_1yr': int(graft_success),
                'survival_months': round(survival_months, 1)
            })

    matches_df = pd.DataFrame(matches)

    print(f"✓ Generated {len(matches_df)} potential matches")
    print(f"  Success rate: {matches_df['graft_success_1yr'].mean():.1%}")

    return matches_df


def validate_data(donors: pd.DataFrame, recipients: pd.DataFrame,
                  matches: pd.DataFrame) -> Dict[str, bool]:
    """
    Perform data quality validation checks.

    Args:
        donors: Donor DataFrame
        recipients: Recipient DataFrame
        matches: Matches DataFrame

    Returns:
        Dictionary of validation results
    """
    print("\nValidating data quality...")

    validations = {}

    # Check for missing values
    validations['donors_no_nulls'] = donors.isnull().sum().sum() == 0
    validations['recipients_no_nulls'] = recipients.isnull().sum().sum() == 0
    validations['matches_no_nulls'] = matches.isnull().sum().sum() == 0

    # Check KDPI range
    validations['kdpi_valid_range'] = (
        (donors['kdpi'] >= 0).all() and (donors['kdpi'] <= 100).all()
    )

    # Check EPTS range
    validations['epts_valid_range'] = (
        (recipients['epts'] >= 0).all() and (recipients['epts'] <= 100).all()
    )

    # Check age ranges
    validations['donor_age_valid'] = (
        (donors['age'] >= 18).all() and (donors['age'] <= 80).all()
    )
    validations['recipient_age_valid'] = (
        (recipients['age'] >= 18).all() and (recipients['age'] <= 80).all()
    )

    # Check match referential integrity
    valid_donor_ids = set(donors['donor_id'])
    valid_recipient_ids = set(recipients['recipient_id'])
    validations['matches_valid_donor_ids'] = matches['donor_id'].isin(valid_donor_ids).all()
    validations['matches_valid_recipient_ids'] = matches['recipient_id'].isin(valid_recipient_ids).all()

    # Print validation results
    all_pass = all(validations.values())
    for check, passed in validations.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}: {passed}")

    if all_pass:
        print("\n✓ All validation checks passed!")
    else:
        print("\n✗ Some validation checks failed!")

    return validations


def save_datasets(donors: pd.DataFrame, recipients: pd.DataFrame,
                  matches: pd.DataFrame, output_dir: str = "data/raw"):
    """
    Save generated datasets to CSV files.

    Args:
        donors: Donor DataFrame
        recipients: Recipient DataFrame
        matches: Matches DataFrame
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving datasets to {output_dir}/...")

    donors.to_csv(output_path / "donors.csv", index=False)
    print(f"  ✓ Saved donors.csv ({len(donors)} records)")

    recipients.to_csv(output_path / "recipients.csv", index=False)
    print(f"  ✓ Saved recipients.csv ({len(recipients)} records)")

    matches.to_csv(output_path / "matches.csv", index=False)
    print(f"  ✓ Saved matches.csv ({len(matches)} records)")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic kidney allocation data"
    )
    parser.add_argument(
        '--n-donors', type=int, default=5000,
        help='Number of donors to generate (default: 5000)'
    )
    parser.add_argument(
        '--n-recipients', type=int, default=3000,
        help='Number of recipients to generate (default: 3000)'
    )
    parser.add_argument(
        '--output-dir', type=str, default='data/raw',
        help='Output directory (default: data/raw)'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    args = parser.parse_args()

    print("="*60)
    print("KIDNEY ALLOCATION DATA GENERATOR")
    print("="*60)
    print(f"Configuration:")
    print(f"  Donors: {args.n_donors}")
    print(f"  Recipients: {args.n_recipients}")
    print(f"  Random Seed: {args.seed}")
    print(f"  Output: {args.output_dir}")
    print("="*60)
    print()

    # Generate data
    donors = generate_donors(args.n_donors, args.seed)
    recipients = generate_recipients(args.n_recipients, args.seed)
    matches = label_outcomes(donors, recipients, args.seed)

    # Validate data
    validations = validate_data(donors, recipients, matches)

    # Save datasets
    if all(validations.values()):
        save_datasets(donors, recipients, matches, args.output_dir)
        print("\n" + "="*60)
        print("DATA GENERATION COMPLETE!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("ERROR: Data validation failed. Files not saved.")
        print("="*60)


if __name__ == "__main__":
    main()
