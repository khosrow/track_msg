# from distutils.core import setup
from setuptools import setup

import track_msg

setup(
    name='track_msg',
    version=track_msg.__version__,
    author=track_msg.__author__,
    author_email='khosrow@khosrow.ca',
    packages=['track_msg'],
    url='https://github.com/khosrow/track_msg',
    license='LICENSE.rst',
    description=track_msg.__doc__.rstrip(),
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': [
            'track_msg = track_msg.track_msg:main',
        ],
    },
)
