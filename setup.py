from setuptools import setup

APP = ['generate-fake-file.py']  # Replace with your script name
DATA_FILES = ['ffg.png'] 
OPTIONS = {
    'argv_emulation': False,
    'packages': ['tkinter'],  # Ensure tkinter is included
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
