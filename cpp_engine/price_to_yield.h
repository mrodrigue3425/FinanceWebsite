#pragma once 

#include <string>
#include <vector>

namespace PriceToYield {
    double find_root();
    std::vector<double> round_to(std::vector<double> vect, int dp);
    std::vector<int> find_k(std::vector<int>);
    std::vector<int> find_d(std::vector<int>);
    double price_to_yield(const std::vector<double>& prices,
                          const std::vector<int>& dtms,
                          const std::vector<double>& coupons);

}