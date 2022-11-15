import pandas
import numpy as np
import argparse

# 
def header(nlinks, SB = True, link_map=None):
    '''
    SB is the switch for sidebands
    '''

    txt = ''
    
    #Sideband option
    if SB: txt = '#Sideband ON\n'
    else: txt = '#Sideband OFF\n'

    #Write link labels
    txt += '#LinkLabel'
    for i in range(nlinks): txt += '           LINK_{:0>2}    '.format(i)

    txt += '\n#BeginData\n'

    return txt

#Side band helper
def ctrl(clk):
    if clk==0: return '0x05'
    # elif clk==(clk_per_evt-1): return '0x00'
    else: return '0x01'

#
def frame(vhexdata, iframe, empty=False, SB=True):

    txt = '0x{0:0>4x}'.format(iframe)

    #Some variable to convert frame valid bits
    scale = 16 ## equals to hexadecimal
    num_of_bits = 4

    for d in vhexdata:

        if not empty:
            #Turn the first bit to 1 for "Frame Valid"

            #Take the 4 leftmost bits
            old_4msb = str(bin(int(d[2], scale))[2:].zfill(num_of_bits))

            #Flip msb to true
            old_4msb = old_4msb.replace('0', '1', 1)

            #Convert it back to an integer
            new_4msb = "%01X" %int(old_4msb, 2)

            #Replace the first hex in the word
            d = d[:2] + new_4msb + d[2 + 1:]
            
        if empty or not SB:
            txt += '    ' + d
        else: #sideband option
            txt += '    ' + ctrl(iframe%frames_per_event) + ' ' + d

    txt += '\n'
    return txt

# 
def empty_frames(n, istart, nlinks, SB=True):
    ''' Make n empty frames for nlinks with starting frame number istart '''

    if SB: empty_data = '0x00 0x0000000000000000'
    else: empty_data ='0x0000000000000000'

    empty_frame = [empty_data] * nlinks
    iframe = istart
    frames = []
    for i in range(n):
        frames.append(frame(empty_frame, iframe, empty=True))
        iframe += 1
    return frames

def convert(infile, outfile, start=6, sideband = True, link_map=None, split=False):

    data = pandas.read_csv(infile,skiprows=1,delim_whitespace=True)
    nlinks = data.Index.max() + 1
    clocks = data.Clock.unique()
    max_clocks = clocks.max()
    nevents = int(np.ceil(clocks.max() / frames_per_event))
    nfiles = int(np.ceil(nevents / events_per_file_hw)) if split else 1
    frames_per_file = frames_per_file_hw if split else nevents * frames_per_event
    print(f'Writing {nevents} events to {nfiles} files')

    for iFile in range(nfiles):
        print(f'  file {iFile}')
        il, ih = iFile * frames_per_file, (iFile + 1) * frames_per_file
        clocks = data.Clock.unique()[il:ih]
        outfilename = outfile.split('.')[0] + '%03d' % iFile + '.txt'
        outf = open(outfilename, 'w')
        outf.write(header(nlinks, link_map=link_map, SB=sideband))

        for f in empty_frames(start, 0, nlinks, SB=sideband):
            outf.write(f)

        iclock = start
        for clock in clocks:
            dt = data[data.Clock == clock].Data
            vhex = ['0x' + d for d in dt]
            outf.write(frame(vhex, iclock, SB=sideband))
            iclock += 1
            if clock % print_freq == 0:
                print("Clock {} / {}".format(clock, max_clocks))

        outf.close()

def link_map():
    the_map = np.zeros(36, dtype='int')
    for i in range(0,3):
        for j in range(6):
            the_map[6*i+j] = 36 + 6*i + j
    for i in range(0,3):
        for j in range(6):
            the_map[6*(i+3)+j] = 56 + 6*i + j
    return the_map

frames_per_event = 54
max_frames_per_file_hw = 1024
frame_offset = 300 # roughly the algorithm latency in clock cycles
events_per_file_hw = int(np.ceil((max_frames_per_file_hw - frame_offset)/ frames_per_event))
frames_per_file_hw = frames_per_event * events_per_file_hw
print_freq = 10000

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--infile', '-i', dest='infile', type=str, default='./proj_deregionizer_emulator_test/solution/csim/build/DeregionizerIn.txt', help='Input file path')
    parser.add_argument('--outfile', '-o', dest='outfile', type=str, default='./source.txt', help='Output file path')
    parser.add_argument('--sideband', '-sb', dest='sideband', action='store_true', help='Sideband option')
    parser.add_argument('--split', '-s', dest='split', action='store_true', help='Split the events across multiple files')
    parser.add_argument('--start', dest='start', type=int, default=12, help='The frame on which to start the event data. Frames before this will be all 0s')
    parser.add_argument('--linkmap', '-l', dest='linkmap', nargs="+", type=int, default=list(range(36)), help='A list mapping physical link indices to deregionizer indices')
    parser.add_argument('--repo-linkmap', dest='repo_linkmap', action='store_true', help='Use the default link mapping. Overrides --linkmap')
    parser.set_defaults(split=False, repo_linkmap=False, sideband=False)
    args = parser.parse_args()

    link_map = link_map() if args.repo_linkmap else args.linkmap
    convert(args.infile, args.outfile, start=args.start, sideband=args.sideband, split=args.split, link_map=link_map)