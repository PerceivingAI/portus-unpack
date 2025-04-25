from pathlib import Path
from setuptools import setup, find_packages

setup(
    name="portus-unpack",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "tiktoken",
    ],
    extras_require={
        "progress": ["tqdm>=4.0"]
    },
    entry_points={
        "console_scripts": [
            "portus-unpack = portus_unpack.__main__:main",
        ]
    },
    author="PerceivingAI",
    description="Portus-Unpack – CLI to unpack & split ChatGPT / Anthropic exports.",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/PerceivingAI/portus-unpack",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
