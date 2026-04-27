from __future__ import annotations

from pathlib import Path


def repair_with_pymeshlab(input_path: str | Path, output_path: str | Path) -> Path:
    """Attempt a conservative PyMeshLab repair pass.

    This is intentionally optional. Mesh repair can alter the object in ways
    that matter aesthetically, so the raw OBJ should always be kept.
    """
    try:
        import pymeshlab
    except ImportError as exc:
        raise RuntimeError(
            "PyMeshLab is not installed. Install with: pip install 'dsp-form-lab[repair]'"
        ) from exc

    source = Path(input_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(source))

    # Function names can shift across PyMeshLab versions. Keep this minimal.
    # In the GUI, use Ctrl-F and search: duplicate, zero area, unreferenced,
    # non manifold, close holes.
    for filter_name in [
        "meshing_remove_duplicate_vertices",
        "meshing_remove_duplicate_faces",
        "meshing_remove_unreferenced_vertices",
        "meshing_remove_null_faces",
    ]:
        try:
            getattr(ms, filter_name)()
        except Exception:
            pass

    ms.save_current_mesh(str(target))
    return target
