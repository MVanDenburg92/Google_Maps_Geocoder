from setuptools import setup, find_packages

setup(
    name='google-maps-geocoder',
    version='0.1.0',
    author='Miles Van Denburg',
    description='A Python module for geocoding addresses using the Google Maps Geocoding API',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'requests',
    ],
    python_requires='>=3.7',
)
