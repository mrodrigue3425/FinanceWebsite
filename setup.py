import setuptools
from setuptools import Extension
from setuptools.command.build_ext import build_ext as _build_ext


# custom build command to find pybind11 headers automatically
class build_ext(_build_ext):
    def finalize_options(self):
        super().finalize_options()
        # this imports the pybind11 package to find where its header files are installed
        import pybind11

        # add the path to the pybind11 headers so the C++ compiler can find them
        self.include_dirs.append(pybind11.get_include())
        self.include_dirs.append(pybind11.get_include(user=True))

    def build_extensions(self):
        if self.compiler.compiler_type == "msvc":
            cxx_std_flag = ["/std=c++17", "/Zi"]
        else:
            cxx_std_flag = ["-std=c++17", "-g"]

        for ext in self.extensions:
            # add the appropriate C++17 flag
            ext.extra_compile_args.extend(cxx_std_flag)

        super().build_extensions()


# define the extension module
ext_modules = [
    Extension(
        # the final installed module name will be 'cpp_engine.cpp_engine'
        name="cpp_engine._cpp_engine",
        # list ALL C++ source files that contain logic or bindings
        sources=["cpp_engine/binding.cpp", "cpp_engine/price_to_yield.cpp"],
        # use C++17 standard for modern features
        language="c++",
    ),
]

# standard setuptools configuration
setuptools.setup(
    name="high-performance-code",
    version="0.1.0",
    description="C++ backend for high-performance financial computation using pybind11.",
    # these packages must be installed *before* setup.py runs its build phase
    setup_requires=["pybind11"],
    install_requires=["Flask"],
    # tell setuptools to include the 'cpp_module' directory as a package
    packages=["cpp_engine"],
    cmdclass={"build_ext": build_ext},
    ext_modules=ext_modules,
)
