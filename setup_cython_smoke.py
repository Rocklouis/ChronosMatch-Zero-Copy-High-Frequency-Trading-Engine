
from setuptools import Extension, setup
from Cython.Build import cythonize

extensions = [
    Extension(
        name="cython_smoke",
        sources=["cython_smoke.pyx"],
    )
]

setup(
    name="cython-smoke-test",
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
    ),
)

