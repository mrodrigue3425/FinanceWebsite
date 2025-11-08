#include "price_to_yield.h"

#include <cmath>
#include <iomanip>
#include <iostream>
#include <vector>

namespace PriceToYield {

const double VN = 100;  // par value in pesos
const int DPP = 182;    // days per coupon period
const int YB = 360;     // year base (in days)

double find_root(double C, int K, int d, double P, int* iterations, double precision) {
    double r_start = 100 * ((C * (360.0 / 182.0)) / P);  // set the initial guess to current yield
    double r_current = r_start;
    double r_next;
    double diff;

    constexpr int MAX_ITERS = 10000;

    int i;

    for (i = 0; i < MAX_ITERS; i++) {
        r_next = r_current - f(r_current, C, K, d, P) / f_prime(r_current, C, K, d);
        diff = std::abs(r_next - r_current);
        if (diff < precision) {
            r_current = r_next;
            break;
        }
        r_current = r_next;
    }

    if (iterations) {
        *iterations = i + 1;
    }

    return r_current;
}

double round_to(double num, int dp) {
    double factor = std::pow(10, dp);
    return std::round(num * factor) / factor;
}

std::vector<double> round_to_vec(std::vector<double> vect, int dp) {
    std::vector<double> rounded_vect(vect.size());
    double factor = std::pow(10, dp);
    for (size_t i = 0; i < vect.size(); i++) {
        rounded_vect[i] = std::round(vect[i] * factor) / factor;
    }
    return rounded_vect;
}

std::vector<int> find_k(std::vector<int> dtms) {
    // this function finds the number of coupon payments left until maturity
    std::vector<int> k(dtms.size());
    for (size_t i = 0; i < dtms.size(); i++) {
        // minus 1 because k should decrease on payment dates
        k[i] = (dtms[i] - 1) / DPP + 1;
    }
    return k;
}

std::vector<int> find_d(std::vector<int> dtms) {
    // this function finds the days accrued in the current period
    std::vector<int> d(dtms.size());
    for (size_t i = 0; i < dtms.size(); i++) {
        // days accrued returns to 0 on payment dates
        d[i] = (DPP - dtms[i] % DPP) == DPP ? 0 : DPP - dtms[i] % DPP;
    }
    return d;
}

double f(double r, double C, int K, int d, double P) {
    double R = 0.01 * r * DPP / YB;
    double alpha = C / pow((1 + R), 1 - 1.0 * d / DPP);
    double beta = C / (R * pow((1 + R), 1 - 1.0 * d / DPP));
    double gamma = C / (R * pow((1 + R), K - 1.0 * d / DPP));
    double sigma = VN / (pow((1 + R), K - 1.0 * d / DPP));

    return alpha + beta - gamma + sigma - C * d / DPP - P;
}

double f_prime(double r, double C, int K, int d) {
    double R = 0.01 * r * DPP / YB;
    double alpha = C * (1.0 * d / DPP - 1) * pow(1 + R, 1.0 * d / DPP - 2);
    double beta = C * ((1 / R) * (1.0 * d / DPP - 1) * pow(1 + R, 1.0 * d / DPP - 2) -
                       (1 / (R * R)) * pow(1 + R, 1.0 * d / DPP - 1));
    double gamma = C * ((1 / R) * (1.0 * d / DPP - K) * pow(1 + R, 1.0 * d / DPP - K - 1) -
                        (1 / (R * R)) * pow(1 + R, 1.0 * d / DPP - K));
    double sigma = VN * (1.0 * d / DPP - K) * pow(1 + R, 1.0 * d / DPP - K - 1);

    return (1.0 * DPP / YB) * (alpha + beta - gamma + sigma);
}

double px(double TC, double r, int K, int d) {
    double R = 0.01 * r * DPP / YB;
    double C = VN * (DPP * 0.01 * TC) / YB;
    double price = (C + C * (1 / R - 1 / (R * pow(1 + R, K - 1))) + VN / pow(1 + R, K - 1)) /
                       pow(1 + R, 1 - 1.0 * d / DPP) -
                   C * 1.0 * d / DPP;
    return price;
}

std::vector<double> price_to_yield(const std::vector<double>& prices, const std::vector<int>& dtms,
                                   const std::vector<double>& coupons) {
    std::vector<double> P = round_to_vec(prices, 6);
    std::vector<double> TC = round_to_vec(coupons, 2);
    std::vector<int> K = find_k(dtms);
    std::vector<int> d = find_d(dtms);
    std::vector<double> C(TC.size());

    // convert coupon rates into cashflows C
    for (size_t i = 0; i < TC.size(); i++) {
        C[i] = VN * ((0.01 * TC[i] * DPP) / YB);
    }

    std::vector<double> yields(prices.size());

    // compute the yields
    for (size_t i = 0; i < yields.size(); i++) {
        double yld = find_root(C[i], K[i], d[i], P[i]);

        // verify by repricing
        double p_check = round_to(px(TC[i], yld, K[i], d[i]), 6);
        double diff = std::abs(p_check - P[i]);

        // if mismatch greater than 2e-6, flag as invalid
        if (diff >= 2e-6 || std::isnan(yld) || std::isinf(yld)) {
            yields[i] = -1.0;
        } else {
            yields[i] = yld;
        }
    }

    return yields;
}
}  // namespace PriceToYield
