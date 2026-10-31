"""Execute notebook walkthroughs without changing the published demo or storing outputs."""

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def execute(path, directory):
    book = nbformat.read(path, as_version=4)
    nbformat.validate(book)
    # Dependency installation and interactive upload/download belong to the user, not QA.
    for cell in book.cells:
        if cell.cell_type == "code":
            cell.source = "\n".join(
                line for line in cell.source.splitlines() if not line.lstrip().startswith("%pip")
            )
    NotebookClient(
        book, timeout=240, kernel_name="python3", resources={"metadata": {"path": str(directory)}}
    ).execute()
    print("Executed:", path.name, flush=True)
    return {"notebook": path.name, "status": "PASS", "outputs_persisted": False}


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    results = []
    with tempfile.TemporaryDirectory(prefix="banking_notebook_qa_") as temp:
        isolated = Path(temp)
        for name in ["src", "config", "sql", "notebooks"]:
            shutil.copytree(
                ROOT / name, isolated / name, ignore=shutil.ignore_patterns("__pycache__")
            )
        for name in [
            "dataset.xlsx",
            "requirements.txt",
            "requirements-pipeline.txt",
            "run_pipeline.py",
        ]:
            shutil.copyfile(ROOT / name, isolated / name)
        names = [
            "00_setup",
            "01_bronze_ingestion",
            "02_silver_transformation",
            "04_data_quality",
            "01_bronze_silver_pipeline",
            "03_gold_business_models",
            "03_gold_business_analysis",
            "05_exploratory_analysis",
            "06_colab_entry",
        ]
        for name in names:
            results.append(execute(isolated / "notebooks" / (name + ".ipynb"), isolated))
    for directory in [ROOT / "ml/notebooks", ROOT / "analytics/notebooks"]:
        for path in sorted(directory.glob("*.ipynb")):
            results.append(execute(path, ROOT))
    output = ROOT / "reports/final_notebook_validation.json"
    output.write_text(
        json.dumps(
            {
                "results": results,
                "executed": len(results),
                "limitations": "Install cells omitted; Colab upload/download UI not exercised. Historical root exploration preserved, not a supported walkthrough.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
