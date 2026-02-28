import libzim
print(f"Libzim Version: {libzim.__version__}")
try:
    print(dir(libzim.Archive))
except:
    print("Could not inspect libzim.Archive")
