"""Run the original Medallion stages; orchestration/run_workflow.py wraps the full platform."""
import argparse
import logging
import os
# Small Excel batches benefit from bounded native-library threads on large-core hosts.
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
from src.pipeline import run
from src.utils.config import DEFAULT_CONFIG


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Banking customer medallion pipeline')
    parser.add_argument('--config', default=str(DEFAULT_CONFIG))
    parser.add_argument('--stage', choices=['all', 'bronze', 'silver', 'quality', 'gold', 'digital'], default='all')
    parser.add_argument('--synthetic-config', help='Digital demo generation/scoring JSON configuration.')
    parser.add_argument('--reuse-synthetic', action='store_true', help='Validate existing raw_synthetic files instead of regenerating them.')
    parser.add_argument('--batch-id')
    parser.add_argument('--source', help='Override the Excel source path (used at ingestion).')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    try:
        if args.stage=='digital':
            from src.synthetic.pipeline import run as run_digital
            batch=run_digital(args.synthetic_config,args.reuse_synthetic)['synthetic_build_id']
        else:
            batch = run(args.config, args.stage, args.batch_id, args.source)
    except Exception as error:
        logging.getLogger('banking').error('Pipeline failed: %s', error)
        raise SystemExit(1) from error
    logging.getLogger('banking').info('Completed %s batch: %s', args.stage, batch)
