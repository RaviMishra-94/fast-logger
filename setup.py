from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fast-logger",
    version="0.1.0",
    author="Ravi Mishra",
    author_email="ravi@paisafintech.com",
    description="A simple, no-fuss logging setup for Python applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RaviMishra-94/fast-logger",
    project_urls={
        "Bug Tracker": "https://github.com/RaviMishra-94/fast-logger/issues",
        "Documentation": "https://github.com/RaviMishra-94/fast-logger/blob/main/README.md",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "fast-logger=fast_logger.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)