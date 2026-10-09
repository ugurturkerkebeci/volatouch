from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="volatouch",
    version="1.0.2",
    author="Uğur Türker Kebeci",
    author_email="167927605+ugurturkerkebeci@users.noreply.github.com",
    description="Ultra-low latency mobile air control & wireless trackpad for PC over Wi-Fi.",
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
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.22.0",
        "websockets>=11.0",
        "mss>=9.0.0",
        "Pillow>=9.0.0",
        "pynput>=1.7.6",
    ],
    extras_require={
        "accelerated": [
            "opencv-python>=4.8.0",
            "numpy>=1.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "volatouch=volatouch.cli:main",
        ],
    },
)
