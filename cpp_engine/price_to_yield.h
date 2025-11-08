#pragma once 

#include <string>
#include <vector>

namespace PriceToYield {
    double find_root(double C, int K, int d, double P,
                     int* iterations = nullptr, double precision = 7e-11);
    double round_to(double num, int dp);
    std::vector<double> round_to_vec(std::vector<double> vect, int dp);
    std::vector<int> find_k(std::vector<int> dtms);
    std::vector<int> find_d(std::vector<int> dtms);
    double f(double r, double C, int K, int d, double P);
    double f_prime(double r, double C, int K, int d);
    std::vector<double> price_to_yield(const std::vector<double>& prices,
                          const std::vector<int>& dtms,
                          const std::vector<double>& coupons);

}