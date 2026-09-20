# -*- coding: utf-8 -*-
"""Pytest plugin to execute the MyST text-notebooks in this directory.

Code below is copied 1:1 from scopesim-targets/docs/conf.py
See also scopesim-targets/docs/notebook_testing.md for more info.
Toasted and by no means final...
"""

import asyncio
import sys
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

import pytest
import yaml


TIMEOUT = 600  # seconds per notebook
STARTUP_TIMEOUT = 120  # seconds to wait for the kernel to come up


def pytest_addoption(parser):
    parser.addoption(
        "--notebooks",
        action="store_true",
        default=False,
        help="Collect and execute the MyST notebooks in docs/.",
    )
    parser.addoption(
        "--notebook-setup",
        default=None,
        metavar="PATH",
        help=(
            "Python file executed in each notebook's kernel before its own "
            "cells. Defaults to _notebook_setup.py next to this conftest, if "
            "present. Use for test-only environment wiring that must not "
            "appear in the published docs."
        ),
    )


def pytest_collect_file(file_path: Path, parent):
    if file_path.suffix != ".md":
        return None
    if ".ipynb_checkpoints" in file_path.parts:
        return None
    if not parent.config.getoption("--notebooks"):
        return None
    if not _is_myst_notebook(_front_matter(file_path.read_text(encoding="utf-8"))):
        return None
    return MystNotebookFile.from_parent(parent, path=file_path)


# --- front matter ----------------------------------------------------------

def _split_front_matter(text: str):
    """Return (front_matter_block, rest) or (None, text)."""
    if not text.startswith("---"):
        return None, text
    _, _, after = text.partition("---\n")
    block, sep, rest = after.partition("\n---")
    if not sep:
        return None, text
    return block, rest.partition("\n")[2]


def _front_matter(text: str) -> dict:
    block, _ = _split_front_matter(text)
    if block is None:
        return {}
    try:
        return yaml.safe_load(block) or {}
    except yaml.YAMLError:
        return {}


def _with_front_matter(text: str, meta: dict) -> str:
    """Splice *meta* back in as the front matter of *text*."""
    _, body = _split_front_matter(text)
    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n" + body


def _is_myst_notebook(meta: dict) -> bool:
    if meta.get("file_format") == "mystnb":
        return True
    text_repr = meta.get("jupytext", {}).get("text_representation", {})
    return text_repr.get("format_name") == "myst"


def _complete_kernelspec(meta: dict) -> bool:
    """Fill in kernelspec fields nbformat requires. True if anything changed.

    A short ``kernelspec: {name: python3}`` is enough for MyST-NB but not for
    nbformat, which requires ``display_name`` too.
    """
    kernelspec = meta.get("kernelspec")
    if not isinstance(kernelspec, dict):
        return False

    name = kernelspec.setdefault("name", "python3")
    changed = False

    if "display_name" not in kernelspec:
        kernelspec["display_name"] = name
        changed = True

    if "language" not in kernelspec:
        kernelspec["language"] = "python" if name.startswith("python") else name
        changed = True

    return changed


def _needs(meta: dict) -> list[str]:
    """Dependencies as ``myst_test: {needs: [...]}`` in front matter."""
    raw = (meta.get("myst_test") or {}).get("needs") or []
    return [raw] if isinstance(raw, str) else list(raw)


def _read_notebook(path: Path):
    import jupytext  # needs to be imported lazily

    text = path.read_text(encoding="utf-8")
    meta = _front_matter(text)

    if _complete_kernelspec(meta):
        text = _with_front_matter(text, meta)

    return jupytext.reads(text, fmt="md:myst")


def _setup_source(config) -> str | None:
    """Test-only preamble, executed in the kernel but never written to disk."""
    override = config.getoption("--notebook-setup")
    path = Path(override) if override else Path(__file__).parent / "_notebook_setup.py"
    if override and not path.exists():
        raise pytest.UsageError(f"--notebook-setup: {path} does not exist")
    return path.read_text(encoding="utf-8") if path.exists() else None


# --- ordering --------------------------------------------------------------

def _components(deps: dict) -> dict:
    """Map each notebook to an id shared by everything it is connected to."""
    parent = {path: path for path in deps}

    def find(path):
        while parent[path] != path:
            parent[path] = parent[parent[path]]
            path = parent[path]
        return path

    for path, targets in deps.items():
        for target in targets:
            root_a, root_b = find(path), find(target)
            if root_a != root_b:
                parent[root_a] = root_b

    return {path: find(path) for path in deps}


# tryfirst is load-bearing: xdist rewrites nodeids to carry the group suffix
# in its own pytest_collection_modifyitems, so a marker added after that hook
# runs is silently ignored and the chain gets scattered across workers.
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    slots = [i for i, item in enumerate(items) if isinstance(item, MystNotebookItem)]
    if not slots:
        return
    by_path = {items[i].path.resolve(): items[i] for i in slots}

    deps = {}
    for path, item in by_path.items():
        targets = []
        for raw in item.needs:
            target = (path.parent / raw).resolve()
            if not target.exists():
                raise pytest.UsageError(
                    f"{item.nodeid}: 'needs' entry {raw!r} does not exist"
                )
            if target in by_path:
                targets.append(target)
            else:
                # Exists, but not part of this run: the notebook cannot
                # legitimately run in isolation, so say so rather than
                # relying on leftovers from a previous run.
                item.unmet.append(raw)
        deps[path] = targets

    try:
        order = list(TopologicalSorter(
            {path: set(targets) for path, targets in deps.items()}
        ).static_order())
    except CycleError as exc:
        raise pytest.UsageError(
            f"circular 'needs' between notebooks: {' -> '.join(str(p) for p in exc.args[1])}"
        ) from exc

    # Pin each chain to one xdist worker; independent notebooks stay free to
    # be distributed. Only add the marker when xdist is actually installed,
    # or --strict-markers rejects it.
    if config.pluginmanager.hasplugin("xdist"):
        groups = _components(deps)
        sizes = {}
        for root in groups.values():
            sizes[root] = sizes.get(root, 0) + 1
        for path, root in groups.items():
            if sizes[root] > 1:
                by_path[path].add_marker(pytest.mark.xdist_group(root.stem))

    for slot, path in zip(slots, [p for p in order if p in by_path]):
        items[slot] = by_path[path]


# --- collection / execution ------------------------------------------------

class MystNotebookFile(pytest.File):
    def collect(self):
        item = MystNotebookItem.from_parent(self, name="notebook")
        item.needs = _needs(_front_matter(self.path.read_text(encoding="utf-8")))
        item.unmet = []
        # Warnings raised in *this* process by zmq/nbclient plumbing must not
        # be turned into errors by the project-wide filterwarnings=error:
        # an exception thrown inside the event loop strands a live kernel.
        # (Warnings from notebook code itself happen in the kernel process.)
        item.add_marker(pytest.mark.filterwarnings("default::RuntimeWarning"))
        item.add_marker(pytest.mark.filterwarnings("default::DeprecationWarning"))
        yield item


def _run(coro):
    """Run *coro* on a loop we fully control, then tear it down.

    On Windows the default Proactor loop cannot do ``add_reader``, which zmq
    needs; pyzmq works around it with an extra tornado selector thread, and
    that combination is what deadlocks past Ctrl+C. A SelectorEventLoop avoids
    the whole mess. Kernels are launched with ``subprocess.Popen`` by
    jupyter_client, not via asyncio, so the selector loop's lack of subprocess
    support is not a problem here.
    """
    if sys.platform == "win32":
        loop = asyncio.SelectorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            loop.run_until_complete(loop.shutdown_asyncgens())

        finally:
            asyncio.set_event_loop(None)
            loop.close()


class MystNotebookItem(pytest.Item):
    def runtest(self):
        from nbclient import NotebookClient # needs to be imported lazily

        if self.unmet:
            pytest.skip(
                f"needs {', '.join(self.unmet)}, not collected in this run"
            )

        notebook = _read_notebook(self.path)

        if notebook.metadata.get("mystnb", {}).get("execution_mode") == "off":
            pytest.skip("execution_mode: off in front matter")
        if not any(cell.cell_type == "code" for cell in notebook.cells):
            pytest.skip("no code cells")

        client = NotebookClient(
            notebook,
            timeout=TIMEOUT,
            startup_timeout=STARTUP_TIMEOUT,
            kernel_name=notebook.metadata["kernelspec"]["name"],
            # run with the notebook's own directory as cwd, like Sphinx does
            resources={"metadata": {"path": str(self.path.parent)}},
        )

        setup = None
        if notebook.metadata.get("myst_test", {}).get("setup") is not False:
            setup = _setup_source(self.config)

        _run(_execute_cells(client, setup=setup))

    def reportinfo(self):
        return self.path, 0, f"myst notebook: {self.path.name}"


async def _execute_cells(client, *, setup: str | None):
    """Execute code cells one at a time, failing at the first error."""
    # need to be imported lazily
    import nbformat
    from nbclient.exceptions import CellExecutionError

    client.reset_execution_trackers()

    async with client.async_setup_kernel():
        if setup:
            cell = nbformat.v4.new_code_cell(setup)
            client.nb.cells.append(cell)
            try:
                await client.async_execute_cell(cell, len(client.nb.cells) - 1)
            except CellExecutionError as exc:
                pytest.fail(f"notebook setup failed:\n{exc}", pytrace=False)
            finally:
                client.nb.cells.pop()

        number = 0
        for index, cell in enumerate(client.nb.cells):
            if cell.cell_type != "code":
                continue
            number += 1

            try:
                await client.async_execute_cell(cell, index)
            except CellExecutionError as exc:
                pytest.fail(
                    f"code cell {number}: {_short_error(exc)}\n\n{exc}",
                    pytrace=False,
                )


def _short_error(exc) -> str:
    """One-line summary for pytest's short summary: the error, not the cell."""
    ename = getattr(exc, "ename", None) or type(exc).__name__
    evalue = (getattr(exc, "evalue", "") or "").strip().splitlines()
    return f"{ename}: {evalue[0]}" if evalue else ename
