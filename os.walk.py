import os
from os.path import join, getsize

s = 0
for root, dirs, files in os.walk(r'C:\Users\yehud\Desktop\temp\AgfaHDC100PlusExp.2002'):
    s += sum(getsize(join(root, name)) for name in files)
print(s)
