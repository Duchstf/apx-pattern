import pandas
import numpy as np
import argparse

def header(nlinks, board='PUPS', link_map=None):
    txt = 'Board {}\n'.format(board)
    txt += 'Quad/Chan :'
    for i in range(nlinks):
        j = i if link_map is None else link_map[i]
        quadstr = '        q{:02d}c{}      '.format(int(j/4), int(j%4))
        txt += quadstr
    txt += '\n      Link :'
    for i in range(nlinks):
        j = i if link_map is None else link_map[i]
        txt += '         {:03d}       '.format(j)
    txt += '\n'
    return txt

def frame(vhexdata, iframe):
    txt = 'Frame {:04d} :'.format(iframe)
    for d in vhexdata:
        txt += ' ' + d
    txt += '\n'
    return txt

def empty_frames(n, istart, nlinks):
    ''' Make n empty frames for nlinks with starting frame number istart '''
    empty_data = '0v0000000000000000'
    empty_frame = [empty_data] * nlinks
    iframe = istart
    frames = []
    for i in range(n):
        frames.append(frame(empty_frame, iframe))
        iframe += 1
    return frames

def convert(infile, outfile, start=6, link_map=None, split=False):
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
        outf.write(header(nlinks, link_map=link_map))
        for f in empty_frames(start, 0, nlinks):
            outf.write(f)
        iclock = start
        for clock in clocks:
            dt = data[data.Clock == clock].Data
            vhex = ['1v' + d for d in dt]
            outf.write(frame(vhex, iclock))
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
    parser.add_argument('--split', '-s', dest='split', action='store_true', help='Split the events across multiple files')
    parser.add_argument('--start', dest='start', type=int, default=12, help='The frame on which to start the event data. Frames before this will be all 0s')
    parser.add_argument('--linkmap', '-l', dest='linkmap', nargs="+", type=int, default=list(range(36)), help='A list mapping physical link indices to deregionizer indices')
    parser.add_argument('--repo-linkmap', dest='repo_linkmap', action='store_true', help='Use the default link mapping. Overrides --linkmap')
    parser.set_defaults(split=False, repo_linkmap=False)
    args = parser.parse_args()

    link_map = link_map() if args.repo_linkmap else args.linkmap
    convert(args.infile, args.outfile, start=args.start, split=args.split, link_map=link_map)
