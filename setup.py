from setuptools import setup, find_packages

setup(
    name="metaclean",
    version="1.0.0",
    description="Universal file metadata inspection and sanitization CLI",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.10",
    packages=find_packages(include=["metaclean", "metaclean.*"]),
    entry_points={"console_scripts": ["metaclean = metaclean.cli:main"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: Android",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
)
