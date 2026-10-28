"""Robust descriptive diagnostics; never removes records or imputes missing data."""
import math
import numpy as np
import pandas as pd


def outliers(frame, config):
    result = frame.copy()
    fences = []
    for col, alias in [('balance', 'balance'), ('estimated_salary', 'salary'), ('credit_score', 'credit_score'), ('age', 'age')]:
        values = frame[col].dropna()
        q1, q3 = values.quantile([.25, .75]) if len(values) else (np.nan, np.nan)
        margin = (q3 - q1) * config['gold']['outlier_iqr_multiplier']
        low, high = q1 - margin, q3 + margin
        result[f'is_{alias}_outlier'] = (frame[col].lt(low) | frame[col].gt(high)).fillna(False)
        fences.append({'variable': col, 'q1': q1, 'q3': q3, 'lower_fence': low, 'upper_fence': high, 'observed_customers': len(values), 'outlier_customers': int(result[f'is_{alias}_outlier'].sum())})
    return result, pd.DataFrame(fences)


def concentration(frame, config):
    observed = frame.loc[frame.balance.notna(), ['customer_key', 'balance']].sort_values(['balance', 'customer_key'], ascending=[False, True])
    n, total = len(observed), observed.balance.sum(min_count=1)
    meaningful = n > 0 and observed.balance.ge(0).all() and total > 0
    rows = []
    for fraction in config['gold']['concentration_fractions']:
        bottom = fraction == .5
        count = math.floor(n * fraction) if bottom else math.ceil(n * fraction)
        subset = observed.tail(count) if bottom else observed.head(count)
        rows.append({'cohort': f'{"Bottom" if bottom else "Top"} {fraction:.0%}', 'requested_fraction': fraction, 'observed_population': n, 'cohort_customers': count, 'observed_balance_total': total, 'cohort_balance': subset.balance.sum(min_count=1) if count else 0.0, 'balance_share': subset.balance.sum() / total if meaningful else np.nan, 'status': 'AVAILABLE' if meaningful else 'UNAVAILABLE_NEGATIVE_OR_NONPOSITIVE_BALANCES', 'rounding_rule': 'floor' if bottom else 'ceil'})
    return pd.DataFrame(rows)


def profiles(frame):
    from .country_summary import aggregate
    rows = []
    for name, mask in [('Premium', frame.customer_value_segment.eq('Premium')), ('High Value', frame.is_high_value), ('High Credit Quality', frame.is_high_credit_quality), ('Long-Term Customer', frame.is_long_tenure)]:
        subset = frame.loc[mask]
        if subset.empty: continue
        for field in ['country', 'gender']:
            part = aggregate(subset, [field]).rename(columns={field: 'profile_member'})
            part.insert(0, 'profile', name)
            part.insert(1, 'profile_dimension', field)
            rows.append(part)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=['profile', 'profile_dimension', 'profile_member', 'total_customers'])
