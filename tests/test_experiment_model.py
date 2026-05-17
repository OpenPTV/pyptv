#!/usr/bin/env python3
"""
High-level tests for the Experiment model.

These tests focus on the Experiment class behavior around:
- Managing Paramsets (add, set active, duplicate, create, rename, delete, remove)
- Persisting to YAML via ParameterManager
- Populating runs from an experiment folder, including legacy-to-YAML conversion
"""

from pathlib import Path
import pytest

from pyptv.experiment import Experiment
from pyptv.parameter_manager import ParameterManager


def write_minimal_yaml(path: Path, num_cams: int = 2, splitter: bool = False):
    """
    Write a minimal YAML parameter set that ParameterManager.from_yaml can load.

    The YAML includes:
    - num_cams
    - ptv: splitter flag (used by get_target_filenames)
    - sequence: base_name list (one per camera in non-splitter mode)
    """
    if splitter:
        # splitter mode uses a single base_name
        content = f"""num_cams: {num_cams}
ptv:
  splitter: true
sequence:
  base_name:
    - img/cam1_00000
"""
    else:
        # non-splitter uses a base_name per camera
        base_names = "\n".join([f"    - img/cam{i+1}_00000" for i in range(num_cams)])
        content = f"""num_cams: {num_cams}
ptv:
  splitter: false
sequence:
  base_name:
{base_names}
"""
    path.write_text(content)


def write_minimal_legacy_dir(dir_path: Path, num_cams: int = 2):
    """
    Create a minimal legacy parameter directory with a valid ptv.par.
    Content mirrors other tests in the suite.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    ptv_par = dir_path / "ptv.par"
    lines = [
        str(num_cams),
    ]
    # add img/cal pairs for each camera
    for i in range(1, num_cams + 1):
        lines.append(f"img/cam{i}.10002")
        lines.append(f"cal/cam{i}.tif")
    # remaining required constants follow real-world examples
    lines.extend([
        "1",      # tiff flag
        "0",      # imx (dummy)
        "1",      # dummy
        "1280",
        "1024",
        "0.012",
        "0.012",
        "0",
        "1",
        "1.33",
        "1.46",
        "6"
    ])
    ptv_par.write_text("\n".join(lines) + "\n")


def test_add_and_set_active_and_basic_roundtrip(tmp_path: Path):
    exp_dir = tmp_path
    yaml_a = exp_dir / "parameters_A.yaml"
    write_minimal_yaml(yaml_a, num_cams=2)

    exp = Experiment()  # fresh Experiment with its own ParameterManager
    # Add a paramset and make it active
    exp.addParamset("A", yaml_a)
    assert exp.nParamsets() == 1
    exp.set_active(0)
    assert exp.active_params is not None
    assert exp.active_params.name == "A"

    # Loading was invoked by set_active; get_n_cam should reflect YAML
    assert exp.get_n_cam() == 2

    # Save should produce/overwrite the YAML without error
    exp.save_parameters()
    assert yaml_a.exists()


def test_duplicate_and_create_new_paramset(tmp_path: Path):
    exp_dir = tmp_path
    yaml_a = exp_dir / "parameters_A.yaml"
    write_minimal_yaml(yaml_a, num_cams=3)

    exp = Experiment()
    exp.addParamset("A", yaml_a)
    exp.set_active(0)

    # Duplicate from active
    dup_yaml = exp.duplicate_paramset("A")
    assert dup_yaml.exists()
    assert dup_yaml.name == "parameters_A_copy.yaml"
    assert any(ps.name == "A_copy" for ps in exp.paramsets)

    # Create a new paramset (copied from active)
    new_yaml = exp.create_new_paramset("B", exp_dir, copy_from_active=True)
    assert new_yaml.exists()
    assert new_yaml.name == "parameters_B.yaml"
    assert any(ps.name == "B" for ps in exp.paramsets)


def test_rename_and_delete_and_remove_paramset(tmp_path: Path):
    exp_dir = tmp_path
    yaml_b = exp_dir / "parameters_B.yaml"
    write_minimal_yaml(yaml_b, num_cams=2)

    exp = Experiment()
    exp.addParamset("B", yaml_b)
    # Not active yet (so we can delete it later)
    assert exp.nParamsets() == 1

    # Rename the paramset and underlying file
    paramset_obj, new_yaml = exp.rename_paramset("B", "C")
    assert paramset_obj.name == "C"
    assert new_yaml.exists()
    assert new_yaml.name == "parameters_C.yaml"
    assert not yaml_b.exists()

    # Create a legacy dir that should be removed by removeParamset
    legacy_dir = new_yaml.parent / "parametersC"
    write_minimal_legacy_dir(legacy_dir, num_cams=2)
    assert legacy_dir.exists()

    # Remove the paramset: should rename YAML to .bck and remove legacy dir
    exp.removeParamset(0)
    assert exp.nParamsets() == 0
    assert not legacy_dir.exists()
    bck = new_yaml.with_suffix(".bck")
    assert bck.exists()

    # Recreate and test delete_paramset (cannot delete active)
    yaml_d = exp_dir / "parameters_D.yaml"
    write_minimal_yaml(yaml_d, num_cams=2)
    exp.addParamset("D", yaml_d)
    exp.set_active(0)
    with pytest.raises(ValueError):
        exp.delete_paramset(0)  # cannot delete the active paramset

    # Add a non-active paramset and delete it
    yaml_e = exp_dir / "parameters_E.yaml"
    write_minimal_yaml(yaml_e, num_cams=2)
    exp.addParamset("E", yaml_e)
    # delete by index 1 (non-active)
    exp.delete_paramset(1)
    assert not yaml_e.exists()
    assert all(ps.name != "E" for ps in exp.paramsets)


def test_populate_runs_converts_legacy_and_loads_yaml(tmp_path: Path):
    exp_dir = tmp_path

    # Legacy run folder that should be converted to YAML
    legacy_run = exp_dir / "parametersRun1"
    write_minimal_legacy_dir(legacy_run, num_cams=2)
    assert (legacy_run / "ptv.par").exists()

    # Existing YAML for another run
    yaml_run2 = exp_dir / "parameters_Run2.yaml"
    write_minimal_yaml(yaml_run2, num_cams=4)

    # Populate
    exp = Experiment()
    exp.populate_runs(exp_dir)

    # Should have both runs present as paramsets
    names = [ps.name for ps in exp.paramsets]
    assert "Run1" in names
    assert "Run2" in names

    # Should have created YAML for legacy Run1
    created_yaml = exp_dir / "parameters_Run1.yaml"
    assert created_yaml.exists()

    # Active set should be loaded and accessible
    assert exp.active_params is not None
    assert isinstance(exp.pm, ParameterManager)
    # After populate, active was set to the first set; ensure get_n_cam is available
    assert isinstance(exp.get_n_cam(), int)