"""Run the synthetic ML extension without rebuilding upstream Medallion datasets."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('MLFLOW_ENABLE_ASYNC_LOGGING','false')
import argparse
from ml.src.utils.config import config,path


def main():
    parser=argparse.ArgumentParser(description='SYNTHETIC DEMO MODEL training and batch scoring')
    parser.add_argument('--config');parser.add_argument('--model',choices=['all','campaign','churn','payroll','service'],default='all')
    parser.add_argument('--stage',choices=['all','features','train','evaluate','register','score'],default='all');parser.add_argument('--score',action='store_true')
    args=parser.parse_args();cfg=config(args.config);stage='score' if args.score else args.stage
    if stage in ['all','features']:
        from ml.src.features.build import build
        build(cfg)
    if stage in ['all','train']:
        from ml.src.training.train import train
        for task in (['campaign','churn','payroll','service'] if args.model=='all' else [args.model]):train(cfg,task)
    if stage in ['evaluate','register']:
        # Evaluation and promotion are one controlled training transaction; never rerun held-out tests.
        from ml.src.registry.store import load
        for task in (['campaign','churn','payroll','service'] if args.model=='all' else [args.model]):
            _,entry=load(cfg,task);print(task,entry['status'],entry['metrics'])
    if stage=='score' or stage=='all' and args.model=='all':
        from ml.src.scoring.batch_score import score
        score(cfg)


if __name__=='__main__':main()
