"""Load selected definitions from a notebook without running the rest of it."""

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(notebook: str, *names: str, **globs) -> dict:
    """Exec only the top-level defs/assignments called `names`; `globs` injects fakes."""
    cells = json.loads((ROOT / notebook).read_text())["cells"]
    src = "\n".join("".join(c["source"]) for c in cells if c["cell_type"] == "code")
    nodes = [
        n
        for n in ast.parse(src).body
        if (isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names)
        or (
            isinstance(n, ast.Assign)
            and any(getattr(t, "id", None) in names for t in n.targets)
        )
    ]
    missing = set(names) - {getattr(n, "name", None) or n.targets[0].id for n in nodes}
    assert not missing, f"not found in {notebook}: {missing}"
    ns = dict(globs)
    exec(compile(ast.Module(nodes, []), notebook, "exec"), ns)  # noqa: S102 - trusted repo notebook
    return ns
