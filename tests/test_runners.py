#!/usr/bin/env python3
"""
Tests for runner methods

File: tests/test_runners.py

Copyright 2024 NeuroML contributors
"""

import logging
import os
import pathlib as pl
import sys
import tempfile
from unittest import mock

import pytest

from pyneuroml.runners import (
    _get_brian2_script_path,
    _run_generated_brian2_script,
    execute_command_in_dir,
    execute_multiple_in_dir,
    generate_sim_scripts_in_folder,
    reload_saved_data,
    run_lems_with_jneuroml_brian2,
    run_multiple_lems_with,
)

from . import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestRunners(BaseTestCase):
    """Test runners module"""

    # Run in top repo dir
    @pytest.fixture(autouse=True)
    def top_dir(self, monkeypatch, request):
        target_dir = request.path.parent.parent
        monkeypatch.chdir(target_dir)

    def test_generate_sim_scripts_in_folder(self):
        """test generate_sim_scripts_in_folder method"""
        thispath = pl.Path(__file__)
        topdirname = str(thispath.parent.parent)
        dirname = generate_sim_scripts_in_folder(
            engine="jneuroml_neuron",
            lems_file_name="LEMS_NML2_Ex5_DetCell.xml",
            root_dir=topdirname + "/examples/",
            run_dir=str(thispath.parent),
        )
        self.assertTrue(pl.Path(dirname).exists())
        self.assertTrue(
            pl.Path(dirname + "/" + pl.Path(dirname).name + "_generated").exists()
        )

    def test_run_multiple_lems_with(self):
        """Test the run_multiple_lems_with function."""

        # compile first, otherwise makes commands fail
        execute_command_in_dir("nrnivmodl", directory="examples")

        spec = {
            "LEMS_NML2_Ex9_FN.xml": {
                "engine": "jneuroml_neuron",
                "args": (),
                "kwargs": {
                    "exec_in_dir": "examples",
                    "nogui": True,
                    "compile_mods": False,
                    "skip_run": True,
                },
            },
            "LEMS_NML2_Ex5_DetCell.xml": {
                "engine": "jneuroml_neuron",
                "args": (),
                "kwargs": {
                    "exec_in_dir": "examples",
                    "nogui": True,
                    "compile_mods": False,
                    "skip_run": True,
                },
            },
        }

        results = run_multiple_lems_with(2, sims_spec=spec)
        for sim, res in results.items():
            self.assertTrue(res())

    def test_execute_multiple_in_dir(self):
        """Test the execute_multiple_in_dir function"""
        cmd_spec = [
            {"command": "ls", "directory": "."},
            {"command": "ls -lash", "directory": "."},
            {"command": "ls -A", "directory": "."},
            {"command": "ls -l", "directory": "."},
        ]

        results = execute_multiple_in_dir(4, cmd_spec)
        for res in results:
            res_one = res()
            self.assertEqual(0, res_one[0])  # return code
            self.assertIn("LICENSE.lesser", res_one[1])

    def test_reload_saved_data(self):
        """Test the reload_saved_data function"""
        lems = """<Lems>
    <Target component="sim"/>
    <Simulation id="sim" length="1ms" step="0.1ms" target="net">
        <EventOutputFile id="ev" fileName="events.dat" format="ID_TIME">
            <EventSelection id="0" select="pop[0]" eventPort="spike"/>
        </EventOutputFile>
        <OutputFile id="out" fileName="traces.dat">
            <OutputColumn id="pop[0]" quantity="pop[0]/v"/>
        </OutputFile>
    </Simulation>
</Lems>
"""
        times = [0.0, 1.0e-4, 2.0e-4, 3.0e-4, 4.0e-4]
        volts = [-0.06, -0.059, -0.058, -0.057, -0.056]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pl.Path(tmpdir)
            (tmp / "sim.xml").write_text(lems)
            (tmp / "traces.dat").write_text(
                "".join(f"{t}\t{v}\n" for t, v in zip(times, volts))
            )
            (tmp / "events.dat").write_text("0\t0.0005\n0\t0.0008\n")

            # traces only (default)
            traces = reload_saved_data("sim.xml", base_dir=tmpdir, plot=False)
            self.assertEqual(traces["t"], times)
            self.assertEqual(traces["pop[0]/v"], volts)

            # events only
            events = reload_saved_data(
                "sim.xml",
                base_dir=tmpdir,
                plot=False,
                reload_events=True,
                reload_traces=False,
            )
            self.assertEqual(events["pop[0]"], [0.0005, 0.0008])

            # both
            traces, events = reload_saved_data(
                "sim.xml", base_dir=tmpdir, plot=False, reload_events=True
            )
            self.assertEqual(len(traces["t"]), len(times))
            self.assertEqual(len(events["pop[0]"]), 2)

            # downsampling
            traces = reload_saved_data(
                "sim.xml", base_dir=tmpdir, plot=False, downsample=2
            )
            # every 2nd row is kept: rows 0, 2 and 4
            self.assertEqual(traces["t"], [0.0, 2.0e-4, 4.0e-4])
            self.assertEqual(traces["pop[0]/v"], [-0.06, -0.058, -0.056])
            self.assertEqual(traces["t"], times[::2])
            self.assertEqual(traces["pop[0]/v"], volts[::2])

            # events are never downsampled
            traces, events = reload_saved_data(
                "sim.xml",
                base_dir=tmpdir,
                plot=False,
                reload_events=True,
                downsample=2,
            )
            self.assertEqual(traces["t"], times[::2])
            self.assertEqual(events["pop[0]"], [0.0005, 0.0008])

            # neither selected is an error
            with self.assertRaises(ValueError):
                reload_saved_data(
                    "sim.xml",
                    base_dir=tmpdir,
                    reload_events=False,
                    reload_traces=False,
                )

    def test_get_brian2_script_path(self):
        """Test that the generated Brian2 script is located next to the LEMS file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = pl.Path(tmpdir).resolve()

            # relative LEMS file: relative to exec_in_dir
            self.assertEqual(
                _get_brian2_script_path("LEMS_sim.xml", tmpdir),
                base / "LEMS_sim_brian2.py",
            )
            self.assertEqual(
                _get_brian2_script_path("sub/LEMS_sim.xml", tmpdir),
                base / "sub" / "LEMS_sim_brian2.py",
            )
            # absolute LEMS file: exec_in_dir does not matter
            self.assertEqual(
                _get_brian2_script_path(str(base / "LEMS_sim.xml"), "elsewhere"),
                base / "LEMS_sim_brian2.py",
            )
            # jNeuroML only replaces a trailing .xml, other extensions are kept
            self.assertEqual(
                _get_brian2_script_path("my-sim.lems", tmpdir),
                base / "my-sim.lems_brian2.py",
            )
            self.assertEqual(
                _get_brian2_script_path("LEMS.xml.sim.xml", tmpdir),
                base / "LEMS.xml.sim_brian2.py",
            )

    def test_run_generated_brian2_script(self):
        """Test running a generated script that is not on the Python path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = pl.Path(tmpdir).resolve()
            # the name has a dash, so it could not be imported with `import`
            script = run_dir / "my-sim_brian2.py"
            script.write_text(
                "import os\n"
                "import sys\n"
                "with open('ran.txt', 'w') as f:\n"
                "    f.write(os.getcwd() + '|' + '|'.join(sys.argv[1:]))\n"
            )

            cwd_before = os.getcwd()
            argv_before = list(sys.argv)
            self.assertNotIn(str(run_dir), sys.path)

            _run_generated_brian2_script(script, tmpdir)

            # ran in exec_in_dir with the gui suppressed
            written = (run_dir / "ran.txt").read_text().split("|")
            self.assertEqual(pl.Path(written[0]).resolve(), run_dir)
            self.assertEqual(written[1:], ["-nogui"])
            # and left the caller's state alone
            self.assertEqual(os.getcwd(), cwd_before)
            self.assertEqual(sys.argv, argv_before)
            self.assertNotIn(str(run_dir), sys.path)

    def test_run_generated_brian2_script_restores_state_on_error(self):
        """Test that sys.argv and the working directory are restored on errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            script = pl.Path(tmpdir) / "LEMS_sim_brian2.py"
            script.write_text("raise RuntimeError('simulation failed')\n")

            cwd_before = os.getcwd()
            argv_before = list(sys.argv)
            # a single entry, as when called from an interactive session
            with mock.patch.object(sys, "argv", argv_before[:1]):
                with self.assertRaises(RuntimeError):
                    _run_generated_brian2_script(script, tmpdir)
                self.assertEqual(sys.argv, argv_before[:1])
            self.assertEqual(os.getcwd(), cwd_before)

            with self.assertRaises(FileNotFoundError):
                _run_generated_brian2_script(
                    pl.Path(tmpdir) / "missing_brian2.py", tmpdir
                )

    def test_run_lems_with_jneuroml_brian2(self):
        """Test that the script next to the LEMS file is run after jnml succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = pl.Path(tmpdir).resolve()
            script = run_dir / "LEMS_sim_brian2.py"
            script.write_text("open('ran.txt', 'w').close()\n")

            # jnml would generate the script: here it already exists
            with mock.patch(
                "pyneuroml.runners.run_jneuroml", return_value=True
            ) as jnml:
                self.assertTrue(
                    run_lems_with_jneuroml_brian2("LEMS_sim.xml", exec_in_dir=tmpdir)
                )
            jnml.assert_called_once()
            self.assertIsFile(run_dir / "ran.txt")

            # nothing is run if jnml fails
            (run_dir / "ran.txt").unlink()
            with mock.patch("pyneuroml.runners.run_jneuroml", return_value=False):
                self.assertFalse(
                    run_lems_with_jneuroml_brian2(
                        "LEMS_sim.xml", exec_in_dir=tmpdir, exit_on_fail=False
                    )
                )
            self.assertFalse((run_dir / "ran.txt").exists())
