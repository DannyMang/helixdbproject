import os
from setuptools import setup

def parse_requirements(filename):
    """
    Load requirements from a pip requirements file.
    This function assumes the file is in a subdirectory relative to setup.py.
    """
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(filepath):
        print(f"Warning: Requirements file not found at '{filepath}'. Skipping.")
        return []

    with open(filepath, 'r') as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]

# Parse the requirements file
# The path is relative to this setup.py file
requirements = parse_requirements('fastapi/requirements.txt')

# Read README for long description, if it exists
try:
    with open('README.md', 'r') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = 'A GitHub App webhook server for automated PR reviews.'


setup(
    name='helix-pr-review-bot',
    version='1.1.0',  # I took this from the FastAPI app version
    author='Your Name',
    author_email='daniel.haidang.ung@gmail.com',
    description='A GitHub App webhook server for automated PR reviews using Cerebras.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dannymang/helixdbproject', # Your project's GitHub URL

    # Since setup.py is in src/, setuptools will look for modules in this directory.
    # We list the .py files that should be included.
    py_modules=['webhook', 'github'],

    install_requires=requirements,

    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',  # Or your chosen license
        'Operating System :: OS Independent',
        'Framework :: FastAPI',
    ],
    python_requires='>=3.8',
)
