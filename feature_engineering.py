"""
Feature Engineering Pipeline for Kidney Allocation

This module loads raw data and creates derived features for ML model training.
Features include binned KDPI, compatibility scores, risk interactions, and
categorical encodings.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import argparse
from pathlib import Path
import joblib


def load_raw_data(data_dir: str = "data/raw") -> tuple:
    """
    Load raw synthetic data from CSV files.

    Args:
        data_dir: Directory containing raw CSV files

    Returns:
        Tuple of (donors_df, recipients_df, matches_df)
    """
    data_path = Path(data_dir)

    print(f"Loading raw data from {data_dir}...")

    donors = pd.read_csv(data_path / "donors.csv")
    recipients = pd.read_csv(data_path / "recipients.csv")
    matches = pd.read_csv(data_path / "matches.csv")

    print(f"  ✓ Loaded {len(donors)} donors")
    print(f"  ✓ Loaded {len(recipients)} recipients")
    print(f"  ✓ Loaded {len(matches)} matches")

    return donors, recipients, matches


def create_derived_features(matches: pd.DataFrame, donors: pd.DataFrame,
                            recipients: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived features from raw match data.

    Features include:
    - KDPI bins (categorical risk tiers)
    - EPTS bins (recipient priority tiers)
    - Age matching quality
    - Risk interaction terms
    - Compatibility indicators

    Args:
        matches: Match data
        donors: Donor data
        recipients: Recipient data

    Returns:
        Enhanced DataFrame with derived features
    """
    print("\nCreating derived features...")

    # Merge full donor and recipient info
    features = matches.copy()

    # Merge donor details
    donor_cols = ['donor_id', 'age', 'sex', 'bmi', 'creatinine',
                  'hcv_positive', 'hypertension', 'diabetes', 'dcd', 'kdpi_category']
    features = features.merge(
        donors[donor_cols],
        on='donor_id',
        how='left',
        suffixes=('', '_donor')
    )

    # Merge recipient details
    recipient_cols = ['recipient_id', 'age', 'sex', 'blood_type', 'pra',
                      'dialysis_years', 'prior_transplant', 'diabetes',
                      'priority_tier', 'wait_points']
    features = features.merge(
        recipients[recipient_cols],
        on='recipient_id',
        how='left',
        suffixes=('', '_recipient')
    )

    # Rename for clarity
    features.rename(columns={
        'age': 'donor_age',
        'sex': 'donor_sex',
        'diabetes': 'donor_diabetes',
        'age_recipient': 'recipient_age',
        'sex_recipient': 'recipient_sex',
        'diabetes_recipient': 'recipient_diabetes'
    }, inplace=True)

    # === DERIVED FEATURES ===

    # 1. KDPI Bins (risk stratification)
    features['kdpi_bin'] = pd.cut(
        features['kdpi'],
        bins=[0, 20, 35, 85, 100],
        labels=['excellent', 'good', 'standard', 'high_risk']
    )

    # 2. EPTS Bins (recipient priority)
    features['epts_bin'] = pd.cut(
        features['epts'],
        bins=[0, 20, 50, 75, 100],
        labels=['very_low', 'low', 'medium', 'high']
    )

    # 3. Age Matching Quality
    features['age_match_quality'] = features['age_diff'].apply(
        lambda x: 'excellent' if x < 10 else (
            'good' if x < 20 else 'poor'
        )
    )

    # 4. Combined Risk Score (KDPI + EPTS interaction)
    # Normalize both to 0-1, then take product (higher = higher risk)
    features['combined_risk'] = (features['kdpi'] / 100) * (features['epts'] / 100)

    # 5. Donor Quality Tier
    features['donor_quality'] = features['kdpi'].apply(
        lambda x: 'premium' if x < 20 else (
            'standard' if x < 85 else 'marginal'
        )
    )

    # 6. Recipient Urgency Score (inverse EPTS + wait time)
    features['urgency_score'] = (
        (100 - features['epts']) * 0.6 +
        features['dialysis_years'] * 10 * 0.4
    )

    # 7. Sensitization Flag (high PRA makes matching difficult)
    features['highly_sensitized'] = (features['pra'] > 80).astype(int)

    # 8. Donor Risk Factors Count
    features['donor_risk_count'] = (
        features['hcv_positive'] +
        features['hypertension'] +
        features['donor_diabetes'] +
        features['dcd']
    )

    # 9. Recipient Risk Factors Count
    features['recipient_risk_count'] = (
        features['prior_transplant'] +
        features['recipient_diabetes'] +
        features['highly_sensitized']
    )

    # 10. Sex Match (same sex donor-recipient)
    features['sex_match'] = (
        features['donor_sex'] == features['recipient_sex']
    ).astype(int)

    # 11. Optimal KDPI-EPTS Match
    # Longevity matching: low EPTS should get low KDPI
    features['longevity_match'] = (
        (features['kdpi'] < 20) & (features['epts'] < 20)
    ).astype(int)

    # 12. Marginal-to-Marginal Match (high risk both sides)
    features['both_high_risk'] = (
        (features['kdpi'] > 85) & (features['epts'] > 85)
    ).astype(int)

    print(f"  ✓ Created {len(features.columns)} total features")

    return features


def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode categorical features for ML models.

    Uses one-hot encoding for nominal variables and preserves
    ordinal encodings where order matters.

    Args:
        df: DataFrame with features

    Returns:
        DataFrame with encoded categorical variables
    """
    print("\nEncoding categorical features...")

    df = df.copy()

    # One-hot encode nominal categoricals
    categorical_cols = [
        'donor_sex', 'recipient_sex', 'blood_type',
        'kdpi_bin', 'epts_bin', 'age_match_quality',
        'donor_quality', 'kdpi_category', 'priority_tier'
    ]

    # Only encode columns that exist
    existing_cats = [col for col in categorical_cols if col in df.columns]

    df_encoded = pd.get_dummies(
        df,
        columns=existing_cats,
        drop_first=True,  # Avoid multicollinearity
        dtype=int
    )

    print(f"  ✓ Encoded {len(existing_cats)} categorical features")
    print(f"  ✓ Total features after encoding: {len(df_encoded.columns)}")

    return df_encoded


def prepare_model_data(df: pd.DataFrame) -> tuple:
    """
    Prepare features and target for model training.

    Args:
        df: Full feature DataFrame

    Returns:
        Tuple of (X, y, feature_names)
    """
    print("\nPreparing model data...")

    # Target variable
    y = df['graft_success_1yr'].values

    # Features to exclude (IDs, targets, raw categoricals already encoded)
    exclude_cols = [
        'donor_id', 'recipient_id',
        'graft_success_1yr', 'survival_months',  # Targets
        'compatibility_score',  # Leakage (derived from outcome)
    ]

    # Select feature columns
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    X = df[feature_cols].values
    feature_names = feature_cols

    print(f"  ✓ Features shape: {X.shape}")
    print(f"  ✓ Target distribution: {np.bincount(y)}")
    print(f"  ✓ Success rate: {y.mean():.1%}")

    return X, y, feature_names


def create_train_test_split(X: np.ndarray, y: np.ndarray,
                            test_size: float = 0.2,
                            random_state: int = 42) -> tuple:
    """
    Split data into training and testing sets.

    Stratified split to maintain class balance.

    Args:
        X: Feature matrix
        y: Target vector
        test_size: Proportion of data for testing
        random_state: Random seed

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    print(f"\nCreating train/test split ({int((1-test_size)*100)}/{int(test_size*100)})...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y  # Maintain class balance
    )

    print(f"  ✓ Training set: {X_train.shape[0]} samples")
    print(f"  ✓ Test set: {X_test.shape[0]} samples")
    print(f"  ✓ Train success rate: {y_train.mean():.1%}")
    print(f"  ✓ Test success rate: {y_test.mean():.1%}")

    return X_train, X_test, y_train, y_test


def scale_features(X_train: np.ndarray, X_test: np.ndarray) -> tuple:
    """
    Standardize features using training set statistics.

    Args:
        X_train: Training features
        X_test: Test features

    Returns:
        Tuple of (X_train_scaled, X_test_scaled, scaler)
    """
    print("\nScaling features...")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"  ✓ Scaled {X_train.shape[1]} features")
    print(f"  ✓ Training mean: {X_train_scaled.mean():.3f}, std: {X_train_scaled.std():.3f}")
    print(f"  ✓ Test mean: {X_test_scaled.mean():.3f}, std: {X_test_scaled.std():.3f}")

    return X_train_scaled, X_test_scaled, scaler


def save_processed_data(X_train: np.ndarray, X_test: np.ndarray,
                       y_train: np.ndarray, y_test: np.ndarray,
                       feature_names: list, scaler: StandardScaler,
                       output_dir: str = "data/processed"):
    """
    Save processed data and preprocessing artifacts.

    Args:
        X_train: Training features
        X_test: Test features
        y_train: Training labels
        y_test: Test labels
        feature_names: List of feature names
        scaler: Fitted scaler object
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving processed data to {output_dir}/...")

    # Save numpy arrays
    np.save(output_path / "X_train.npy", X_train)
    np.save(output_path / "X_test.npy", X_test)
    np.save(output_path / "y_train.npy", y_train)
    np.save(output_path / "y_test.npy", y_test)

    # Save feature names
    with open(output_path / "feature_names.txt", 'w') as f:
        f.write('\n'.join(feature_names))

    # Save scaler
    joblib.dump(scaler, output_path / "scaler.pkl")

    print(f"  ✓ Saved training data: {X_train.shape}")
    print(f"  ✓ Saved test data: {X_test.shape}")
    print(f"  ✓ Saved {len(feature_names)} feature names")
    print(f"  ✓ Saved scaler object")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Feature engineering for kidney allocation data"
    )
    parser.add_argument(
        '--input-dir', type=str, default='data/raw',
        help='Input directory with raw CSV files (default: data/raw)'
    )
    parser.add_argument(
        '--output-dir', type=str, default='data/processed',
        help='Output directory for processed data (default: data/processed)'
    )
    parser.add_argument(
        '--test-size', type=float, default=0.2,
        help='Test set proportion (default: 0.2)'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed (default: 42)'
    )

    args = parser.parse_args()

    print("="*60)
    print("FEATURE ENGINEERING PIPELINE")
    print("="*60)
    print(f"Configuration:")
    print(f"  Input: {args.input_dir}")
    print(f"  Output: {args.output_dir}")
    print(f"  Test Size: {args.test_size}")
    print(f"  Random Seed: {args.seed}")
    print("="*60)
    print()

    # Load raw data
    donors, recipients, matches = load_raw_data(args.input_dir)

    # Create derived features
    features = create_derived_features(matches, donors, recipients)

    # Encode categorical features
    features_encoded = encode_categorical_features(features)

    # Prepare model data (X, y)
    X, y, feature_names = prepare_model_data(features_encoded)

    # Train/test split
    X_train, X_test, y_train, y_test = create_train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed
    )

    # Scale features
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)

    # Save processed data
    save_processed_data(
        X_train_scaled, X_test_scaled,
        y_train, y_test,
        feature_names, scaler,
        args.output_dir
    )

    print("\n" + "="*60)
    print("FEATURE ENGINEERING COMPLETE!")
    print("="*60)
    print("\nSummary:")
    print(f"  Total features: {len(feature_names)}")
    print(f"  Training samples: {len(y_train)}")
    print(f"  Test samples: {len(y_test)}")
    print(f"  Class balance (train): {y_train.mean():.1%} success")
    print(f"  Class balance (test): {y_test.mean():.1%} success")


if __name__ == "__main__":
    main()
