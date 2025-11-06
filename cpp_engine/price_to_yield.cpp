#include "price_to_yield.h"
#include <iostream>
#include <vector>
#include <cmath>

namespace PriceToYield {

    const double VN = 100; // par value in pesos
    const int DPP = 182; // days per coupon period
    const int YB = 360; // year base (in days)

    double find_root(){
        // TODO: implement conversion from price to yield
        return 0.0;
    }

    std::vector<double> round_to(std::vector<double> vect, int dp){
        std::vector<double> rounded_vect(vect.size());
        double factor = std::pow(10, dp);
        for(int i = 0; i < vect.size(); i++){
            rounded_vect[i] = std::round(vect[i] * factor) / factor;
        }
        return rounded_vect;
    }

    std::vector<int> find_k (std::vector<int> dtms){
        // this function finds the number of coupon payments left until maturity
        std::vector<int> k(dtms.size());
        for (int i = 0; i < dtms.size(); i++){
            // minus 1 because k should decrease on payment dates
            k[i] = (dtms[i] - 1)/DPP;
        }
        return k;
    }

    std::vector<int> find_d (std::vector<int> dtms){
        // this function finds the days accrued in the current period
        std::vector<int> d(dtms.size());
        for (int i = 0; i < dtms.size(); i++){
            // days accrued returns to 0 on payment dates
            d[i] = (DPP - dtms[i] % DPP) == DPP ? 0 : DPP - dtms[i] % DPP;
        }
        return d;
    }

    double price_to_yield(const std::vector<double>& prices,
                          const std::vector<int>& dtms,
                          const std::vector<double>& coupons){

        std::vector<double> P = round_to(prices, 6);
        std::vector<double> TC = round_to(coupons, 2);
        std::vector<int> K = find_k(dtms);
        std::vector<int> d = find_d(dtms);

        std::vector<double> yields(prices.size());

        return 0.0;
    }
}
