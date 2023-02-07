from setuptools import find_packages
from setuptools import setup


with open("requirements.txt") as file:
    requirements = file.read()


setup(
    name="Data Ingestion Prep: ASISA Flows Data",
    description="Prep CIS Fund and Analysis sheets for Star Schema",
    packages=find_packages(),
    package_requires=requirements,
)
