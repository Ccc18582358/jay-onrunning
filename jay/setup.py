import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Jay", 
    version="0.0.1",
    author="jinanlongen.com",
    author_email="dev@jinanlongen.com",
    description="E-commerce crawler core",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jinanlongen/jay",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
