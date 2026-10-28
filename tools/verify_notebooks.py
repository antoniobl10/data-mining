"""Execute stage notebooks without persisting customer previews in Git."""
from pathlib import Path
import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import nbformat
from nbclient import NotebookClient


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    order = {'01_bronze_ingestion.ipynb': 0, '02_silver_transformation.ipynb': 1, '04_data_quality.ipynb': 2, '01_bronze_silver_pipeline.ipynb': 3}
    for path in sorted((root / 'notebooks').glob('*.ipynb'), key=lambda p: (order.get(p.name, 10), p.name)):
        book = nbformat.read(path, as_version=4)
        nbformat.validate(book)
        if path.name not in ['01_bronze_ingestion.ipynb', '01_bronze_silver_pipeline.ipynb', '02_silver_transformation.ipynb', '04_data_quality.ipynb']:
            print(f'Schema validated: {path.name}')
            continue
        # Dependencies are already installed by the test environment; upload/export remain disabled.
        book.cells = [cell for cell in book.cells if cell.cell_type != 'code' or not cell.source.startswith('%pip')]
        NotebookClient(book, timeout=180, kernel_name='python3', resources={'metadata': {'path': str(root / 'notebooks')}}).execute()
        print(f'Executed: {path.name}')
