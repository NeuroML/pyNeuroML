from pyneuroml import pynml

run_dir = '.'

commands = ['pwd', 'ls -alt testss']

for command in commands:

    print("\n====================\n")

    returncode, output = pynml.execute_command_in_dir(command, run_dir, prefix="Output [%s] > "%command, verbose=True)

    print('  ----  Return code from execute_command_in_dir: %s; output: \n%s\n--------------------------'%(returncode, output))

    success = pynml.execute_command_in_dir_with_realtime_output(command, run_dir, prefix="Output [%s]: "%command, verbose=False)

    print('  ----  Success of execute_command_in_dir_with_realtime_output: %s'%success)
