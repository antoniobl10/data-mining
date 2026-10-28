"""Source-level check report and persisted Silver exploration, independent of Gold."""
from pathlib import Path
from src.quality.checks import quality_report
from src.ingestion.bronze_ingestion import atomic_json


def generate_data_quality_report(bronze, config, batch_id, checks=None):
    report = quality_report(bronze, config, batch_id)
    if checks is not None:
        later = checks.duplicate_later_source_row
        percentage = float(later.mean() * 100) if len(later) else 0.0
        q = config['quality']
        report.loc[len(report)] = ['duplicate_later_source_row', len(later), int(later.sum()), percentage, 'FAIL' if percentage > q['fail_threshold'] else 'WARNING' if percentage > q['warning_threshold'] else 'PASS', report.run_timestamp.iloc[0], batch_id]
    return report


def persist_quality_report(report, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    report.to_parquet(folder / 'data_quality_report.parquet', index=False)
    report.to_csv(folder / 'data_quality_report.csv', index=False)


def exploration_summary(bronze, result, report, folder):
    summary = {
        'bronze_rows': len(bronze), 'silver_rows': len(result.customers), 'quarantine_rows': len(result.quarantine),
        'retained_unique_source_customers': int(result.all_records.customer_id.nunique()),
        'silver_unique_customers': int(result.customers.customer_id.nunique()),
        'duplicate_statistics': result.duplicate_statistics,
        'source_missing_values': {name.removeprefix('missing_'): int(row.failed_records) for name, row in report.set_index('check_name').iterrows() if name.startswith('missing_')},
        'source_checks': report.set_index('check_name').failed_records.astype(int).to_dict(),
        'all_record_statuses': result.all_records.data_quality_status.value_counts().to_dict(),
        'silver_distributions': {col: result.customers[col].value_counts(dropna=False).to_dict() for col in ['country', 'gender', 'age_group', 'credit_score_band', 'balance_band', 'salary_band', 'tenure_band']},
    }
    atomic_json(Path(folder) / 'exploration_summary.json', summary)
    return summary
