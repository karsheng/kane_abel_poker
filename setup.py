from setuptools import setup, find_packages

setup(
    name="kane_abel_poker",
    version="0.1",
    packages=find_packages(include=["src"]),
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
