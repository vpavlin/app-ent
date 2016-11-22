import sys
from dpyexec import Shipy

shipy_client = Shipy()
shipy_client.shipy(sys.argv[1:])
