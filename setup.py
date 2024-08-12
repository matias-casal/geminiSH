"""
Setup module for the GeminiSH application.
"""

from setuptools import setup, find_packages

setup(
    name="geminiSH",
    version="1.0.0",
    packages=find_packages(),
    description="Tool based on Google`s Gemini to work on diferents code bases.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Matias Casal",
    author_email="tempo-rices01@icloud.com",
    url="https://github.com/matias-casal/geminiSH",
    install_requires=[
        "google-generativeai",
        "prompt_toolkit",
        "rich",
        "screeninfo",
        "pyautogui",
        "pyperclip",
        "sounddevice",
        "soundfile",
        "pydub",
        "unidiff",
    ],
    entry_points={
        "console_scripts": [
            "geminiSH=geminiSH.main:main",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: Spanish",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
