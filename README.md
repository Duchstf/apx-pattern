# Generate input pattern files for APx framework
---

## Steps

* Start by running the Deregionizer emulator in `correlator-common/l2-deregionizer/ref like vivado_hls -f test_deregionizer_emulator.tcl {nevents=1000 write=1} .`
  * This reads the dump files, so you can use the 1000 events TTbar + 200 PU files in the repo (the script default) or produce some other dump file to do more events / different samples. 

* That will produce a file `proj_deregionizer_emulator_test/solution/csim/build/DeregionizerIn.txt`:
  * On Serenity / emp-fwk, that can be converted to pattern files with `rufl_file_to_pfile_emp.py` script.
  * On Apx framework, it can be converted to pattern files with `rufl_file_to_pfile_APx.py`
  * The script can be run, for example, like the following:
    ```
    python rufl_file_to_pfile_APx.py -o pattern_files_APd/source.txt -s
    ```
    
    * The `i` option for the input file, that defaults to the one produced by the Vivado HLS script above
    * The `s` means split the events across multiple files of 1024 lines each (for hardware buffers), if you omit it you get one long file (that you can use in simulation)
    * There’s a `l` option to specify a ‘link map’ to specify the physical link index connected to the deregionizer input at that position. So if you’ve connected deregionizer input 0 to board link 10 it’d start `l 10 …`. It should be a list of 36 values. The default is just `list(range(36))`
    * `-repo-linkmap` to use the mapping corresponding to the `link_map.vhd` ordering in the correlator-layer2 build.
