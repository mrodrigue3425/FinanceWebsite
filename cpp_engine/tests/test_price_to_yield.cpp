#include <gtest/gtest.h>
#include "../price_to_yield.h"
#include <cmath>
#include <random>
#include <vector>
#include <chrono>

constexpr int DPP = 182;
constexpr double VN = 100;
constexpr int YB = 360;

double px(double TC, double r, int K, int d);
double round_to(double num, int dp);

std::random_device rd;

std:: uniform_real_distribution<> dist_r(1e-6,20);
std:: uniform_int_distribution<> dist_K(1,50);
std:: uniform_int_distribution<> dist_TC(0,29);
std:: uniform_int_distribution<> dist_d(0,181);


TEST(FindKTest, BasicCase) {
    std::vector<int> test_input = {1092,1093,1091};
    std::vector<int> result = PriceToYield::find_k(test_input);
    std::vector<int> expected_output = {5, 6, 5};
    EXPECT_EQ(result, expected_output);
}

TEST(FindDTest, BasicCase) {
    std::vector<int> test_input = {182,183,181};
    std::vector<int> result = PriceToYield::find_d(test_input);
    std::vector<int> expected_output = {0, 181, 1};
    EXPECT_EQ(result, expected_output);
}

TEST(fTest, BasicCase) {
    double r  = 6.0;
    double C = 4.55;
    int K = 22;
    int d = 87;
    double P = 102.733288;
    double result = PriceToYield::f(r,C,K,d,P);
    double expected_output = 20.96746668;
    EXPECT_NEAR(result, expected_output, 1e-8);  
    
}

TEST(fTest, BasicCase2) {
    double r  = 6.012846;
    double C = 4.55;
    int K = 15;
    int d = 22;
    double P = 81.723424;
    double result = PriceToYield::f(r,C,K,d,P);
    double expected_output = 36.13091135;
    EXPECT_NEAR(result, expected_output, 1e-8);  
    
}

TEST(f_primeTest, BasicCase) {
    double r  = 6.012846;
    double C = 4.55;
    int K = 15;
    int d = 22;
    double result = PriceToYield::f_prime(r,C,K,d);
    double expected_output = -662.8384541;
    EXPECT_NEAR(result, expected_output, 1e-8); 
    
}

TEST(f_primeTest, BasicCase2) {
    double r  = 9.234159;
    double C = 3.538888889;
    int K = 34;
    int d = 156;
    double result = PriceToYield::f_prime(r,C,K,d);
    double expected_output = -725.451976;
    EXPECT_NEAR(result, expected_output, 1e-7); 
    
}

TEST(f_primeTest, NonZero) {

    //std::mt19937 gen(rd());
    std::mt19937 gen(42);

    int num_test = 5000;
    
    std::vector<double> TCs(30);

    for (int i = 0; i < 30; i++) TCs[i] = (i + 1) / 2.0;

    // generate test data
    std::vector<double> r; r.resize(num_test);
    std::vector<double> P; P.resize(num_test);
    std::vector<double> TC; TC.resize(num_test);
    std::vector<double> K; K.resize(num_test);
    std::vector<double> d; d.resize(num_test);
    
    for(int i=0;i<num_test; i++){
        TC[i] = TCs[dist_TC(gen)];
        K[i] = dist_K(gen);
        d[i] = dist_d(gen);
        r[i] = round_to(dist_r(gen),6);
        P[i] = round_to(px(TC[i], r[i], K[i], d[i]),6);
    }

    //test fprime
    double fprime;

    for (int i = 0; i<num_test;i++) {
        fprime = PriceToYield::f_prime(
        r[i], VN*((0.01*TC[i]*DPP)/YB),
        K[i],d[i]);


        EXPECT_GT(std::abs(fprime), 1e-12)
        << "f_prime near zero for r=" << r[i]
        << ", TC=" << TC[i]
        << ", K=" << K[i]
        << ", d=" << d[i];
    }

}

TEST(find_rootTest, BasicCase) {

    //std::mt19937 gen(rd());
    std::mt19937 gen(42);

    using namespace std::chrono;

    int num_test = 10000;

    double precision = 1.5e-11;

    std::vector<double> TCs(30);
    for (int i = 0; i < 30; i++){
        TCs[i] = (i+1)/2.0;
    }
    // generate test data
    std::vector<double> r; r.resize(num_test);
    std::vector<double> P; P.resize(num_test);
    std::vector<double> TC; TC.resize(num_test);
    std::vector<double> K; K.resize(num_test);
    std::vector<double> d; d.resize(num_test);
    
    for(int i=0;i<num_test; i++){
        TC[i] = TCs[dist_TC(gen)];
        K[i] = dist_K(gen);
        d[i] = dist_d(gen);
        r[i] = dist_r(gen);
        P[i] = round_to(px(TC[i], r[i], K[i], d[i]),6);
    }

    // test find_root
    double r_result;
    double P_result;
    double P_expected;
    double diff = 0; double max_diff = 0; double av_diff = 0;
    double av_time; 
    int total_iters = 0; int max_iters = 0; double av_iters = 0;
    int failures = 0;
    
    auto start = high_resolution_clock::now();
    for (int i = 0; i<num_test; i++){

        int iters;        

        r_result = PriceToYield::find_root(
        VN*((0.01*TC[i]*DPP)/YB),
        K[i],d[i],P[i], &iters, precision);

        P_result = round_to(px(TC[i],r_result, K[i], d[i]),6);
        P_expected = P[i];

        double this_diff = std::abs(P_result-P_expected);
        diff += this_diff;
        max_diff = std::max(max_diff, this_diff);

        total_iters += iters;
        max_iters = std::max(max_iters, iters);

        if (P_result != P_expected) {
            failures++;
        }

        EXPECT_EQ(P_result, P_expected)
        << "Failed case " << i
        << " | TC=" << TC[i]
        << " K=" << K[i]
        << " d=" << d[i]
        << " r_true=" << r[i]
        << " r_found=" << r_result
        << " | P_expected=" << P_expected
        << " | P_result=" << P_result
        << " | diff=" << std::abs(P_result - P_expected);
    }
    auto end = high_resolution_clock::now();
    av_time = duration_cast<microseconds>(end - start).count()/1000.0/num_test;
    av_diff = diff/num_test;
    av_iters = 1.0*total_iters/num_test;
    double failure_pct = 100.0 * failures / num_test;
    std::cout << std::endl
              << "SUMMARY | Precision: " << precision
              << " | Tests: " << num_test << std::endl
              << "==========================================" <<std::endl
              << " | Avg diff: " << av_diff
              << " | Max diff: " << max_diff << std::endl
              << " | Avg iters: " << av_iters
              << " | Max iters: " << max_iters << std::endl
              << " | Avg time: " << av_time << " ms" <<std::endl
              << "==========================================" <<std::endl
              << " Fail count: "<< failures 
              << " | Failure rate: " << failure_pct << "%" 
              << std::endl << std::endl;
}



TEST(find_rootTest, PrecisionSweep) {
    
    //std::mt19937 gen(rd());
    std::mt19937 gen(42);
    using namespace std::chrono;

    const int num_test = 10000;

    std::vector<double> TCs(30);
    for (int i = 0; i < 30; i++) TCs[i] = (i + 1) / 2.0;

    std::vector<double> r(num_test);
    std::vector<double> P(num_test);
    std::vector<double> TC(num_test);
    std::vector<int> K(num_test);
    std::vector<int> d(num_test);

    for (int i = 0; i < num_test; i++) {
        TC[i] = TCs[dist_TC(gen)];
        K[i] = dist_K(gen);
        d[i] = dist_d(gen);
        r[i] = dist_r(gen);
        P[i] = round_to(px(TC[i], r[i], K[i], d[i]), 6);
    }

    // sweep over different precisions 
    std::vector<double> precision_values = {1e-11, 5e-11, 6e-11, 7e-11,
                                            7.5e-11, 8e-11, 8.5e-11,
                                            9e-11, 9.5e-11, 1e-10, 1.5e-10};

    for (auto precision_value : precision_values) {

        double diff_sum = 0, max_diff = 0;
        double time_sum = 0;
        int total_iters = 0, max_iters = 0;
        int fail_count = 0;

        for (int i = 0; i < num_test; i++) {
            int iters;

            auto start = high_resolution_clock::now();
            double r_result = PriceToYield::find_root(
                VN * ((0.01 * TC[i] * DPP) / YB),
                K[i], d[i], P[i], &iters, precision_value
            );
            auto end = high_resolution_clock::now();

            double elapsed_ms = duration_cast<microseconds>(end - start).count() / 1000.0;
            time_sum += elapsed_ms;
            max_iters = std::max(max_iters, iters);
            total_iters += iters;

            double P_result = round_to(px(TC[i], r_result, K[i], d[i]),6);
            double P_expected = P[i];
            double this_diff = std::abs(P_result - P_expected);
            diff_sum += this_diff;
            max_diff = std::max(max_diff, this_diff);

            if (P_result != P_expected) fail_count++;
        }

        double avg_diff = diff_sum / num_test;
        double avg_time = time_sum / num_test;
        double avg_iters = 1.0 * total_iters / num_test;
        double fail_rate = 100.0 * fail_count / num_test;

        std::cout << std::endl
              << "SUMMARY | Precision: " << precision_value
              << " | Tests: " << num_test << std::endl
              << "==========================================" <<std::endl
              << " | Avg diff: " << avg_diff
              << " | Max diff: " << max_diff << std::endl
              << " | Avg iters: " << avg_iters
              << " | Max iters: " << max_iters << std::endl
              << " | Avg time: " << avg_time << " ms" <<std::endl
              << "==========================================" <<std::endl
              << " Fail count: "<< fail_count 
              << " | Failure rate: " << fail_rate << "%" 
              << std::endl << std::endl;
    }
}

TEST(price_to_yieldTest, BasicCase) {
    
    //std::mt19937 gen(rd());
    std::mt19937 gen(42);

    std::vector<double> prices = {102.643974, 102.129601, 97.313866, 90.112654, 88.326678};
    std::vector<int> dtms = {874, 1602, 2785, 6243, 10156};
    std::vector<double> coupon_rates = {8.500000, 8.500000, 7.500000, 7.750000, 8.000000};

    std::vector<int> K = PriceToYield::find_k(dtms);
    std::vector<int> d = PriceToYield::find_d(dtms);

    std::vector<double> yields = PriceToYield::price_to_yield(
                prices, dtms, coupon_rates
            );

    double P_result;
    double P_expected;
    for (int i = 0; i<prices.size(); i++){
        P_result = round_to(px(coupon_rates[i], yields[i],
        K[i], d[i]),6);
        P_expected = prices[i];
        EXPECT_EQ(P_result, P_expected);
    }
}
double px(double TC, double r, int K, int d){
    double R = 0.01*r*DPP/YB;
    double C = VN*(DPP*0.01*TC)/YB;
    double price = (C + C * (1 / R - 1 / (R * pow(1 + R, K - 1)))
                + VN / pow(1 + R, K - 1))/ pow(1 + R, 1 - 1.0*d / DPP)
                - C * 1.0*d / DPP;

    return price;
}


double round_to(double num, int dp){

    double factor = std::pow(10, dp);
  
    return std::round(num * factor) / factor;
}

