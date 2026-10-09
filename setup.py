from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="volatouch",
    version="1.2.0",
    author="Uğur Türker Kebeci",
    author_email="167927605+ugurturkerkebeci@users.noreply.github.com",
    description="Zero-dependency ultra-low latency bidirectional remote control for PC and Android phone over Wi-Fi.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ugurturkerkebeci/volatouch",
    project_urls={
        "Bug Tracker": "https://github.com/ugurturkerkebeci/volatouch/issues",
        "Source Code": "https://github.com/ugurturkerkebeci/volatouch",
    },
    packages=find_packages(include=["volatouch", "volatouch.*"]),
    package_data={
        "volatouch": ["web/**/*", "web/*"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Hardware",
        "Topic :: Multimedia :: Graphics :: Capture",
    ],
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "volatouch=volatouch.cli:main",
        ],
    },
)
