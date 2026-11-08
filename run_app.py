import sys
from monitor.cli import main

if __name__ == '__main__':
    sys.argv = ['monitor', '-c', 'example.yaml']
    main()
