"""Run source → Bronze → Silver → Gold; the final Power BI report is a later phase."""
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
    parser.add_argument('--stage', choices=['all', 'bronze', 'silver', 'quality', 'gold'], default='all')
    parser.add_argument('--batch-id')
    parser.add_argument('--source', help='Override the Excel source path (used at ingestion).')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    try:
        batch = run(args.config, args.stage, args.batch_id, args.source)
    except Exception as error:
        logging.getLogger('banking').error('Pipeline failed: %s', error)
        raise SystemExit(1) from error
    logging.getLogger('banking').info('Completed %s batch: %s', args.stage, batch)
