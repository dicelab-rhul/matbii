from setuptools import setup, find_packages

ICUA2_VERSION = "2.0.2"
setup(
    name="matbii",
    version="0.0.2",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="A configurable implementation of the MATB-II: Multi-Attribute Task Battery.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dicelab-rhul/icua/tree/main/example/matbii",
    packages=find_packages(),
    install_requires=[f"icua=={ICUA2_VERSION}"],
    extras_require={
        "tobii": [f"icua[tobii]=={ICUA2_VERSION}"],
    },
    python_requires=">=3.10",
    package_data={
        "matbii.tasks": ["**/*.sch", "**/*.schema.json", "**/*.svg.jinja"],
    },
)
