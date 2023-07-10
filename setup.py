import os
from setuptools import setup, find_packages


def read(f_name):
    return open(os.path.join(os.path.dirname(__file__), f_name)).read()


setup(
    name='azote',
    version='1.12.3',
    description='Wallpaper manager for sway and some other WMs',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["images/*", "langs/*"]
    },
    url='https://github.com/nwg-piotr/azote',
    license='GPL3',
    author='Piotr Miller',
    author_email='nwg.piotr@gmail.com',
    python_requires='>=3.8.0',
    install_requires=[],
)
