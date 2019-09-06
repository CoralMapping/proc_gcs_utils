import setuptools


with open("README.md", "r") as f:
    long_description = f.read()


setuptools.setup(
    name="proc-gcs-utils",
    version="0.0.1",
    description="Utility functions for Google Cloud Storage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['proc_gcs_utils'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
