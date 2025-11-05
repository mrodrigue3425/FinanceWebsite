#include "price_to_yield.h"
#include <iostream>

namespace PriceToYield {
    std::string say_hello() {
        std::cout << "This is a test output from the price_to_yield cpp source file." << std::endl;
        return "Python Call Succeeded";
    }  

    double px_to_yld(){
        // TODO: implement conversion from price to yield
        return 0.0;
    }

    double run(){
        std::cout << "Running yield-to-price... " << std::endl;
        say_hello();
        return 0.0;
    }
}
