"""Execute Gold-only analysis without committing customer data outputs."""
from pathlib import Path
import asyncio
import sys
if sys.platform=='win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import nbformat
from nbclient import NotebookClient

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    path=root/'notebooks/03_gold_business_analysis.ipynb'
    book=nbformat.read(path,as_version=4)
    nbformat.validate(book)
    NotebookClient(book,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(root/'notebooks')}}).execute()
    print('Executed Gold-only business analysis notebook successfully.')
