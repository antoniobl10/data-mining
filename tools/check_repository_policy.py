"""Lightweight source policy; emits filenames, never matching secret values."""
import argparse
from pathlib import Path
import re
import subprocess
import yaml
from src.utils.config import UniqueKeyLoader

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"), re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), re.compile(r"dapi[0-9a-f]{32}")]


def check(files):
    errors = []
    for file in files:
        if not file.is_file():
            continue
        if file.stat().st_size > 10 * 1024 * 1024:
            errors.append(str(file.relative_to(ROOT)) + ': file exceeds 10 MiB source policy')
            continue
        if file.suffix.lower() in {'.png','.jpg','.pdf','.xlsx','.pbix','.parquet','.dll'}:
            if file.suffix.lower() in {'.xlsx','.pbix','.parquet','.dll'}:
                errors.append(str(file.relative_to(ROOT)) + ': restricted runtime/data artifact')
            continue
        try:
            text=file.read_text(encoding='utf-8')
        except (UnicodeError,OSError):
            continue
        if any(pattern.search(text) for pattern in PATTERNS):
            errors.append(str(file.relative_to(ROOT)) + ': possible credential pattern; inspect locally')
        if file.suffix in {'.yaml','.yml'}:
            try:
                yaml.load(text,Loader=UniqueKeyLoader)
            except (ValueError,yaml.YAMLError) as error:
                errors.append(str(file.relative_to(ROOT)) + ': invalid YAML: ' + type(error).__name__)
        if file.name.startswith('.env') and file.name!='.env.example':
            errors.append(str(file.relative_to(ROOT)) + ': environment file must not be versioned')
    return errors


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--staged',action='store_true');args=parser.parse_args()
    command=['git','diff','--cached','--name-only','--diff-filter=ACM'] if args.staged else ['git','ls-files','--cached','--others','--exclude-standard']
    files=subprocess.check_output(command,cwd=ROOT,text=True).splitlines()
    errors=check([ROOT/f for f in files])
    if errors:
        raise SystemExit('\n'.join(errors))
    print('Repository secret-pattern/YAML/size policy passed for',len(files),'source files; heuristic scan is not a secret-free guarantee.')


if __name__=='__main__':main()
