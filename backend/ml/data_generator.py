import os
import sys
import pandas as pd
import numpy as np

# Column order standard
FEATURE_COLUMNS = [
    'amount',
    'failure_type',
    'payment_method',
    'customer_history',
    'retry_number',
    'time_since_failure_hours',
    'card_issuer'
]

def generate_synthetic_data(n_samples=10000, seed=42):
    """Generate synthetic payment transaction data for ML training and baseline validation"""
    np.random.seed(seed)
    
    failure_types = ['soft_decline', 'hard_decline', 'timeout', 'duplicate']
    payment_methods = ['card', 'upi', 'netbanking']
    customer_histories = ['good', 'medium', 'bad']
    card_issuers = ['HDFC', 'ICICI', 'SBI', 'Axis', 'None']
    
    amounts = np.round(np.random.uniform(100, 50000, n_samples), 2)
    selected_failures = np.random.choice(failure_types, n_samples, p=[0.4, 0.2, 0.3, 0.1])
    selected_methods = np.random.choice(payment_methods, n_samples, p=[0.5, 0.3, 0.2])
    selected_histories = np.random.choice(customer_histories, n_samples, p=[0.3, 0.4, 0.3])
    retry_numbers = np.random.randint(1, 4, n_samples)
    time_since_hours = np.random.randint(0, 72, n_samples)
    selected_issuers = np.random.choice(card_issuers, n_samples, p=[0.2, 0.2, 0.15, 0.15, 0.3])
    
    # Store raw dataframe
    raw_df = pd.DataFrame({
        'amount': amounts,
        'failure_type': selected_failures,
        'payment_method': selected_methods,
        'customer_history': selected_histories,
        'retry_number': retry_numbers,
        'time_since_failure_hours': time_since_hours,
        'card_issuer': selected_issuers
    })
    
    # Generate recovery labels based on realistic payment patterns
    raw_df['is_recoverable'] = 0
    
    # 1. Soft declines: 65% recoverable if customer is good or medium
    soft_mask = raw_df['failure_type'] == 'soft_decline'
    good_medium_mask = raw_df['customer_history'].isin(['good', 'medium'])
    soft_eligible = soft_mask & good_medium_mask
    raw_df.loc[soft_eligible, 'is_recoverable'] = (
        np.random.rand(soft_eligible.sum()) < 0.65
    ).astype(int)
    
    # Soft declines for bad customer history: ~20% recoverable
    soft_bad = soft_mask & (~good_medium_mask)
    raw_df.loc[soft_bad, 'is_recoverable'] = (
        np.random.rand(soft_bad.sum()) < 0.20
    ).astype(int)
    
    # 2. Network Timeouts: 75% recoverable (temporary gateway outage/congestion)
    timeout_mask = raw_df['failure_type'] == 'timeout'
    raw_df.loc[timeout_mask, 'is_recoverable'] = (
        np.random.rand(timeout_mask.sum()) < 0.75
    ).astype(int)
    
    # 3. Hard declines: only 15% recoverable (e.g. invalid CVV, card blocked, insufficient funds)
    hard_mask = raw_df['failure_type'] == 'hard_decline'
    raw_df.loc[hard_mask, 'is_recoverable'] = (
        np.random.rand(hard_mask.sum()) < 0.15
    ).astype(int)
    
    # 4. Duplicates: 0% recoverable
    raw_df.loc[raw_df['failure_type'] == 'duplicate', 'is_recoverable'] = 0
    
    # Penalize repeated retries slightly: later retries have lower success rate
    higher_retry_mask = raw_df['retry_number'] >= 3
    to_flip_to_0 = higher_retry_mask & (raw_df['is_recoverable'] == 1) & (np.random.rand(n_samples) < 0.3)
    raw_df.loc[to_flip_to_0, 'is_recoverable'] = 0

    return raw_df

def encode_dataset(df):
    """Encode categorical features into numeric format for model training"""
    encoded_df = df.copy()
    
    failure_map = {'soft_decline': 0, 'hard_decline': 1, 'timeout': 2, 'duplicate': 3}
    encoded_df['failure_type'] = encoded_df['failure_type'].map(failure_map).fillna(3).astype(int)
    
    payment_map = {'card': 0, 'upi': 1, 'netbanking': 2}
    encoded_df['payment_method'] = encoded_df['payment_method'].map(payment_map).fillna(2).astype(int)
    
    history_map = {'bad': 0, 'medium': 1, 'good': 2}
    encoded_df['customer_history'] = encoded_df['customer_history'].map(history_map).fillna(0).astype(int)
    
    encoded_df['card_issuer'] = (encoded_df['card_issuer'] != 'None').astype(int)
    
    # Ensure column order matches FEATURE_COLUMNS + ['is_recoverable']
    cols = FEATURE_COLUMNS + ['is_recoverable']
    return encoded_df[cols]

if __name__ == '__main__':
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(project_root, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"Generating 10,000 synthetic transaction records...")
    raw_data = generate_synthetic_data(n_samples=10000)
    
    csv_path = os.path.join(data_dir, 'synthetic_data.csv')
    raw_data.to_csv(csv_path, index=False)
    print(f"Saved synthetic dataset to: {csv_path}")
    print(f"Dataset summary:\n{raw_data['failure_type'].value_counts()}")
    print(f"Recovery rate: {raw_data['is_recoverable'].mean() * 100:.2f}%")
