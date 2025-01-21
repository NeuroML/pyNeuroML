from pyneuroml import pynml

command = 'pwd'
command = 'ls -alt test'
run_dir = '.'

returncode, output = pynml.execute_command_in_dir(command, run_dir, prefix="Command [%s]> "%command, verbose=True) 

print('  ----  Return code from execute_command_in_dir: %s; output: \n%s\n--------------------------'%(returncode, output))

success = pynml.execute_command_in_dir_with_realtime_output(command, run_dir, prefix="Command [%s]: "%command, verbose=False) 

print('  ----  Success of execute_command_in_dir_with_realtime_output: %s'%success)