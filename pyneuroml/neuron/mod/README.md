## Converting mod files to NeuroML 2 channel files

This script can be used to extract information from a mod file about states, ions, etc. and generate an initial NeuroML 2 file for the channel.

**Work in progress.** See https://github.com/NeuroML/NeuroML2/issues/101.

To test this out try:

     python parse_mod_file.py ../../../examples/NaConductance.mod

and look at NaConductance.channel.nml 
