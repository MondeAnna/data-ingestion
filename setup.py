from setuptools import setup


with open("requirements.txt") as file:
    requirements = file.read()


setup(
    name="Data Ingestion Prep: ASISA Flows Data",
    description="Prep CIS Fund and Analysis sheets for Star Schema",
    packages=["utilities"],
    package_requires=requirements,
)
