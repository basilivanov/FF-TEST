import sys, pkgutil, requests
print("requests:", requests.__version__, requests.__file__)
import requests.adapters as a
print("Has BaseAdapter:", hasattr(a, "BaseAdapter"))
print("sys.path[0]:", sys.path[0])
