import argparse

from brik import Brik, BrikOpts, CompilerPlatform

def main():
    parser = argparse.ArgumentParser(
        prog='brik',
        description='brik interpreter',
        epilog=''
    )

    parser.add_argument('-f', '--file')
    parser.add_argument('-o', '--out', default='bin')
    parser.add_argument('-v', '--verbose', action='store_true')

    parser.add_argument('-l32', dest='platform', action='store_const', const=CompilerPlatform.LINUX_X86_32)
    parser.add_argument('-l64', dest='platform', action='store_const', const=CompilerPlatform.LINUX_X86_64)
    parser.add_argument('-w32', dest='platform', action='store_const', const=CompilerPlatform.WINDOWS_X86_32)
    parser.add_argument('-w64', dest='platform', action='store_const', const=CompilerPlatform.WINDOWS_X86_64)

    args = parser.parse_args()
    if not args.file:
        print('No filename provided')
        exit()
    else:
        proj_name = args.file.split('\\')[-1].split('.')[0]
        with open(args.file, 'r') as f:
            source = f.read()
        print(f'Compiling project {proj_name}')
        opts = BrikOpts(
            proj_name,
            args.platform if args.platform else CompilerPlatform.LINUX_X86_64,
            args.out,
            args.verbose
        )
        compiler = Brik(opts)
        results = compiler.compile_all(source)

if __name__ == '__main__':
    main()
