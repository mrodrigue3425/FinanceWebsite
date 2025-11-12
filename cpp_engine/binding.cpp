#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "price_to_yield.h"

namespace py = pybind11;

PYBIND11_MODULE(_cpp_engine, m) {
    m.doc() = "Pybind11 high-performance code for financial models.";

    m.def("price_to_yield", &PriceToYield::price_to_yield,
          "Runs the price-to-yield calculation in C++.");
}
