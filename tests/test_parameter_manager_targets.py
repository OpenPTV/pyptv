#!/usr/bin/env python3
"""
Unit tests for ParameterManager.get_target_filenames.

Covers both splitter and non-splitter modes and verifies that output paths
are computed from YAML contents in a predictable way.
"""

from pathlib import Path
from pyptv.parameter_manager import ParameterManager


def write_yaml(path: Path, num_cams: int, splitter: bool, base_names):
    """
    Helper to write a minimal YAML file covering the fields used by
    get_target_filenames: num_cams, ptv.splitter, sequence.base_name.
    """
    lines = [f"num_cams: {num_cams}"]
    lines.append("ptv:")
    lines.append(f"  splitter: {'true' if splitter else 'false'}")
    lines.append("sequence:")
    lines.append("  base_name:")
    for bn in base_names:
        lines.append(f"    - {bn}")
    path.write_text("\n".join(lines) + "\n")


def test_get_target_filenames_splitter_mode(tmp_path: Path):
    """
    In splitter mode:
    - Only the first base_name is used to determine the folder.
    - The function returns cam1..camN in that folder, where N=num_cams.
    """
    yaml_path = tmp_path / "params.yaml"
    write_yaml(
        yaml_path,
        num_cams=4,
        splitter=True,
        base_names=["img/cam_basename_00000"],  # only one base_name required
    )

    pm = ParameterManager()
    pm.from_yaml(yaml_path)
    targets = pm.get_target_filenames()
    # Expect 4 camera folders in the same parent directory as the single base name
    assert len(targets) == 4
    assert all(t.parent.name == "img" for t in targets)
    assert [t.name for t in targets] == ["cam1", "cam2", "cam3", "cam4"]


def test_get_target_filenames_non_splitter_mode(tmp_path: Path):
    """
    In non-splitter mode:
    - One base_name is expected per camera.
    - The output list length equals len(base_names) (even if < num_cams).
    - Each output path is the parent folder of the provided base_name joined with 'cam{i}'.
    """
    yaml_path = tmp_path / "params.yaml"
    base_names = [
        "run/img1_00000",
        "run/img2_00000",
        "run/img3_00000",
    ]
    write_yaml(
        yaml_path,
        num_cams=4,              # deliberately greater than len(base_names)
        splitter=False,
        base_names=base_names,
    )

    pm = ParameterManager()
    pm.from_yaml(yaml_path)
    targets = pm.get_target_filenames()
    # Expect as many targets as base_names provided
    assert len(targets) == len(base_names)
    # Parent folder for each is 'run'
    assert all(t.parent.name == "run" for t in targets)
    # cam index is based on enumerate position (1-based)
    assert [t.name for t in targets] == ["cam1", "cam2", "cam3"]