
from setuptools import Extension, setup
from Cython.Build import cythonize

extensions = [
    Extension(
        name="chronosmatch.matching_core",
        sources=["src/chronosmatch/matching_core.pyx"],
    )
]

setup(
    name="chronosmatch-core",
    packages=["chronosmatch"],
    package_dir={"chronosmatch": "src/chronosmatch"},
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
    ),
)
