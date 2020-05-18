import setuptools


with open("README.md", "r") as f:
    long_description = f.read()


setuptools.setup(
    name="proc-gcs-utils",
    version="1.0.1",
    description="Utility functions for Google Cloud Storage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['proc_gcs_utils'],
    install_requires=['google-cloud-storage==1.16.1'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0 Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    url='https://github.com/CoralMapping/proc_gcs_utils'
)
