from distutils.core import setup, Extension

module1 = Extension('niall', sources=['_niall.c', 'niall.c'])

setup(name='python-niall',
       version='1.0',
       description='Niall python bindings',
       ext_modules=[module1])
