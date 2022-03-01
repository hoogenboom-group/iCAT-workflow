from setuptools import setup

DISTNAME = "iCAT-workflow"
DESCRIPTION = "Post-processing workflow for volume CLEM image data."
MAINTAINER = "Ryan Lane"
MAINTAINER_EMAIL = "r.i.lane@tudelft.nl"
LICENSE = "LICENSE"
URL = "https://github.com/lanery/iCAT-workflow"
VERSION = "0.1.dev"
PACKAGES = [
    "icatapi",
]
INSTALL_REQUIRES = [
    "beautifulsoup4",
    "matplotlib",
    "numpy",
    "pandas",
    "render-python",
    "scipy",
    "scikit-image",
    "seaborn",
    "shapely",
]

if __name__ == '__main__':

    setup(
        name=DISTNAME,
        version=VERSION,
        author=MAINTAINER,
        author_email=MAINTAINER_EMAIL,
        packages=PACKAGES,
        include_package_data=True,
        url=URL,
        license=LICENSE,
        description=DESCRIPTION,
        long_description=open("README.md").read(),
        install_requires=INSTALL_REQUIRES,
    )
