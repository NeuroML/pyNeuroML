from pyneuroml import pynml


command = "python snooze.py"
run_dir = "."

oo = pynml.execute_command_in_dir_with_realtime_output(command, run_dir, verbose=True)

print(oo)
