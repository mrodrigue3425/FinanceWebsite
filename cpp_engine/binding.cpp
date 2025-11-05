#include <pybind11/pybind11.h>
#include "price_to_yield.h" 

namespace py = pybind11;

PYBIND11_MODULE(_cpp_engine, m) {

    m.doc() = "Pybind11 high-performance code for financial models."; 

    m.def("say_hello", &FinancialEngine::say_hello, "A test function that returns a string and prints a message from C++.");
}

