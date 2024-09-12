import os, argparse, glob
import numpy as np

def main():

    #Load in the arguments
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--msfile', '-f', dest='msfile', help='Input ms file name')
    parser.add_argument('--version', '-v', dest='version', help='Flag version name')
    parser.add_argument('--flag',    action='store_true', help='Flagging')
    parser.add_argument('--no-flag', action='store_false', dest='flag', help='No Flagging')

    args = parser.parse_args()
    msfile = args.msfile
    version = args.version
    flag = args.flag

    # Output parameters to the terminal 
    print('Restoring Flag version {} for ms file {}'.format(version,msfile))
  
    flagmanager(vis = msfile, mode='restore', versionname=version)      
        
    if flag:
        if '_S.ms' in msfile:
            print("Flaggin S-band")
            # include other desired flags for S band
        if '_C.ms' in msfile:
            print("Flaggin C-band")
            # include other desired flags for C band
        if '_X.ms' in msfile:
            print("Flaggin X-band")
            # include other desired flags for X band
    else:
        print("Not Flaggin'")
        
if __name__ == "__main__":
    main()
