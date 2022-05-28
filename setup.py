from setuptools import setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="mongo_manager",
    author="Clutter Development",
    version="1.0.0",
    license="MIT",
    description="A simple PyMongo wrapper.",
    install_requires=requirements,
    python_requires=">=3.10",
    py_modules=["mongo_manager"],
    packages=["mongo_manager"],
)
