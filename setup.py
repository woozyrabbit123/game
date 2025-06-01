from setuptools import setup, find_packages

setup(
    name="narco-syndicate",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pygame",
        "textual",
    ],
    python_requires=">=3.10",
)
