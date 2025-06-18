import os
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Folders and files to ignore completely
IGNORE_FOLDERS = {'.git', '__pycache__', '.pytest_cache', 'instance', 'venv'}
IGNORE_FILES = {'.DS_Store', 'kroger.db'}

README_PATH = 'README.md'
START_TAG = '<!-- STRUCTURE_START -->'
END_TAG = '<!-- STRUCTURE_END -->'

def generate_structure(path, prefix=""):
    entries = sorted(os.listdir(path))
    structure = ""

    for index, entry in enumerate(entries):
        if entry in IGNORE_FOLDERS or entry.startswith(".") or entry in IGNORE_FILES:
            continue

        full_path = os.path.join(path, entry)
        connector = "└── " if index == len(entries) - 1 else "├── "
        structure += prefix + connector + entry + "\n"

        if os.path.isdir(full_path):
            new_prefix = prefix + ("    " if index == len(entries) - 1 else "│   ")
            structure += generate_structure(full_path, new_prefix)

    return structure

def update_readme_with_structure(structure):
    if not os.path.exists(README_PATH):
        logger.error("❌ README.md not found.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    block = f"{START_TAG}\n```\n{structure.strip()}\n```\n{END_TAG}"

    if START_TAG in content and END_TAG in content:
        content = re.sub(f"{START_TAG}.*?{END_TAG}", block, content, flags=re.DOTALL)
    else:
        logger.warning(
            "⚠️ STRUCTURE markers not found in README.md. Add them under the Project Structure section."
        )
        return

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("✅ README.md updated with project structure.")

if __name__ == "__main__":
    project_root = "."
    structure = generate_structure(project_root)
    structure_text = "Project Structure - Kroger Price Alert\n\n" + structure

    # Save to .txt file
    with open("PROJECT_STRUCTURE.txt", "w") as f:
        f.write(structure_text)
    logger.info("✅ Project structure saved to PROJECT_STRUCTURE.txt")

    # Update README.md
    update_readme_with_structure(structure)
