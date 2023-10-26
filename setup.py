from setuptools import setup, find_packages

setup(
    name='renderer',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'torch',
        'pytorch3d',
        'pillow',
        'numpy',
        'tqdm',
        'PyYAML',
        'plotly',
        'matplotlib',
        'pandas'
    ],
    entry_points={
        'console_scripts': [
            'render=renderer.rendering_script:main',
        ],
    },
)