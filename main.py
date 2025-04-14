from setuptools import setup, find_packages

setup(
    name='conversation-archiver',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'tiktoken',
        'beautifulsoup4',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'archive-tool=conversation_archiver.__main__:main'
        ]
    },
    author='PerceivingAI',
    description='A CLI tool to extract and archive ChatGPT conversations.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/PerceivingAI/conversation-archiver',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent'
    ],
    python_requires='>=3.8',
)
