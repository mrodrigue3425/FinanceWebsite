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
std::vector<double> px_vec(std::vector<double> TC_vec,
                           std::vector<double> r_vec,
                           std::vector<int> K_vec,
                           std::vector<int>  d_vec);

std::random_device rd;

std:: uniform_real_distribution<> dist_r(1e-6,20);
std:: uniform_int_distribution<> dist_K(1,50);
std:: uniform_int_distribution<> dist_TC(0,29);
std:: uniform_int_distribution<> dist_d(0,181);


TEST(FindKTest, BasicCase) {
    const std::vector<int> test_input = {1092,1093,1091, 183, 182, 1};
    const std::vector<int> result = PriceToYield::find_k(test_input);
    const std::vector<int> expected_output = {6, 7, 6, 2, 1, 1};
    EXPECT_EQ(result, expected_output);
}

TEST(FindDTest, BasicCase) {
    const std::vector<int> test_input = {182,183,181};
    const std::vector<int> result = PriceToYield::find_d(test_input);
    const std::vector<int> expected_output = {0, 181, 1};
    EXPECT_EQ(result, expected_output);
}

TEST(fTest, BasicCase) {
    const double r  = 6.0;
    const double C = 4.55;
    const int K = 22;
    const int d = 87;
    const double P = 102.733288;
    const double result = PriceToYield::f(r,C,K,d,P);
    const double expected_output = 20.96746668;
    EXPECT_NEAR(result, expected_output, 1e-8);  
    
}

TEST(fTest, BasicCase2) {
    const double r  = 6.012846;
    const double C = 4.55;
    const int K = 15;
    const int d = 22;
    const double P = 81.723424;
    const double result = PriceToYield::f(r,C,K,d,P);
    const double expected_output = 36.13091135;
    EXPECT_NEAR(result, expected_output, 1e-8);  
    
}

TEST(f_primeTest, BasicCase) {
    const double r  = 6.012846;
    const double C = 4.55;
    const int K = 15;
    const int d = 22;
    const double result = PriceToYield::f_prime(r,C,K,d);
    const double expected_output = -662.8384541;
    EXPECT_NEAR(result, expected_output, 1e-8); 
    
}

TEST(f_primeTest, BasicCase2) {
    const double r  = 9.234159;
    const double C = 3.538888889;
    const int K = 34;
    const int d = 156;
    const double result = PriceToYield::f_prime(r,C,K,d);
    const double expected_output = -725.451976;
    EXPECT_NEAR(result, expected_output, 1e-7); 
    
}

TEST(f_primeTest, NonZero) {

    //std::mt19937 gen(rd());
    std::mt19937 gen(42);

    const int num_test = 5000;
    
    std::vector<double> TCs(30);

    for (int i = 0; i < 30; i++) TCs[i] = (i + 1) / 2.0;

    // generate test data
    std::vector<double> r; r.resize(num_test);
    std::vector<double> P; P.resize(num_test);
    std::vector<double> TC; TC.resize(num_test);
    std::vector<int> K; K.resize(num_test);
    std::vector<int> d; d.resize(num_test);
    
    for(int i=0;i<num_test; i++){
        TC[i] = TCs[dist_TC(gen)];
        K[i] = dist_K(gen);
        d[i] = dist_d(gen);
        r[i] = round_to(dist_r(gen),6);
        P[i] = round_to(px(TC[i], r[i], K[i], d[i]),6);
    }

    //test fprime
    

    for (int i = 0; i<num_test;i++) {
        const double fprime = PriceToYield::f_prime(
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

    const int num_test = 10000;

    const double precision = 1.5e-11;

    std::vector<double> TCs(30);
    for (int i = 0; i < 30; i++){
        TCs[i] = (i+1)/2.0;
    }
    // generate test data
    std::vector<double> r; r.resize(num_test);
    std::vector<double> P; P.resize(num_test);
    std::vector<double> TC; TC.resize(num_test);
    std::vector<int> K; K.resize(num_test);
    std::vector<int> d; d.resize(num_test);
    
    for(int i=0;i<num_test; i++){
        TC[i] = TCs[dist_TC(gen)];
        K[i] = dist_K(gen);
        d[i] = dist_d(gen);
        r[i] = dist_r(gen);
        P[i] = round_to(px(TC[i], r[i], K[i], d[i]),6);
    }

    // test find_root
    double r_result = 0;
    double P_result = 0;
    double P_expected = 0;
    double diff = 0; double this_diff = 0; double max_diff = 0; double av_diff = 0;
    double av_time = 0; 
    int total_iters = 0; int max_iters = 0; double av_iters = 0;
    int failures = 0;
    double failure_pct = 0;
    
    auto start = high_resolution_clock::now();
    for (int i = 0; i<num_test; i++){

        int iters = 0;        

        r_result = PriceToYield::find_root(
        VN*((0.01*TC[i]*DPP)/YB),
        K[i],d[i],P[i], &iters, precision);

        P_result = round_to(px(TC[i],r_result, K[i], d[i]),6);
        P_expected = P[i];

        this_diff = std::abs(P_result-P_expected);
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

    // performance metrics
    av_time = static_cast<double>(duration_cast<microseconds>(end - start).count())/1000.0/num_test;
    av_diff = diff/num_test;
    av_iters = 1.0*total_iters/num_test;
    failure_pct = 100.0 * failures / num_test;

    std::cout << "\n"
              << "SUMMARY | Precision: " << precision
              << " | Tests: " << num_test << "\n"
              << "==========================================" << "\n"
              << " | Avg diff: " << av_diff
              << " | Max diff: " << max_diff << "\n"
              << " | Avg iters: " << av_iters
              << " | Max iters: " << max_iters << "\n"
              << " | Avg time: " << av_time << " ms" << "\n"
              << "==========================================" <<  "\n"
              << " Fail count: "<< failures 
              << " | Failure rate: " << failure_pct << "%" 
              << "\n\n";
}



TEST(find_rootTest, PrecisionSweep) {
    
    //std::mt19937 gen(rd());
    std::mt19937 gen(42);
    using namespace std::chrono;

    const int num_test = 2000;

    std::vector<double> TCs(30);
    for (int i = 0; i < 30; i++) TCs[i] = (i + 1) / 2.0;

    std::vector<double> r(num_test);
    std::vector<double> P(num_test);
    std::vector<double> TC(num_test);
    std::vector<int> K(num_test);
    std::vector<int> d(num_test);

    const int fail_count = 0;

    for (int i = 0; i < num_test; i++) {
        TC[i] = TCs[dist_TC(gen)];
        K[i] = dist_K(gen);
        d[i] = dist_d(gen);
        r[i] = dist_r(gen);
        P[i] = round_to(px(TC[i], r[i], K[i], d[i]), 6);
    }

    // sweep over different precisions 
    const std::vector<double> precision_values = {1e-11, 5e-11, 6e-11, 7e-11,
                                            7.5e-11, 8e-11, 8.5e-11,
                                            9e-11, 9.5e-11, 1e-10, 1.5e-10};

    for (auto precision_value : precision_values) {

        double P_result = 0;
        double P_expected = 0;
        double diff_sum = 0; double this_diff = 0; double max_diff = 0;
        int total_iters = 0, max_iters = 0;
        int fail_count = 0;
        double r_result = 0;

        double avg_diff = 0;
        double avg_time = 0;
        double avg_iters = 0;
        double fail_rate = 0;       

        auto start = high_resolution_clock::now();
        for (int i = 0; i < num_test; i++) {

            int iters = 0;
            
            r_result = PriceToYield::find_root(
                VN * ((0.01 * TC[i] * DPP) / YB),
                K[i], d[i], P[i], &iters, precision_value
            );

            max_iters = std::max(max_iters, iters);
            total_iters += iters;

            P_result = round_to(px(TC[i], r_result, K[i], d[i]),6);
            P_expected = P[i];

            this_diff = std::abs(P_result - P_expected);
            diff_sum += this_diff;
            max_diff = std::max(max_diff, this_diff);

            if (P_result != P_expected) fail_count++;
        }
        auto end = high_resolution_clock::now();

        // performance metrics
        avg_diff = diff_sum / num_test;
        avg_time = static_cast<double>(duration_cast<microseconds>(end - start).count())/1000.0/num_test;
        avg_iters = 1.0 * total_iters / num_test;
        fail_rate = 100.0 * fail_count / num_test;

        std::cout << "\n"
              << "SUMMARY | Precision: " << precision_value
              << " | Tests: " << num_test << "\n"
              << "==========================================" "\n"
              << " | Avg diff: " << avg_diff
              << " | Max diff: " << max_diff << "\n"
              << " | Avg iters: " << avg_iters
              << " | Max iters: " << max_iters << "\n"
              << " | Avg time: " << avg_time << " ms" << "\n"
              << "==========================================" << "\n"
              << " Fail count: "<< fail_count 
              << " | Failure rate: " << fail_rate << "%" 
              << "\n\n";
    }
}

TEST(price_to_yieldTest, BasicCase) {
    
    //std::mt19937 gen(rd());
    std::mt19937 gen(42);
    using namespace std::chrono;

    std:: uniform_real_distribution<> dist_m(1e-7,1e-4);
    std:: uniform_int_distribution<> dist_pm(1,2);
    std:: uniform_int_distribution<> dist_dtm(1,10000);

    const int num_test = 2000;
    const int num_mbonos = 5;
    
    std::vector<double> TCs(30);

    for (int i = 0; i < 30; i++){
        TCs[i] = (i+1)/2.0;
    }

    using Matrix_double = std::vector<std::vector<double>>;
    using Matrix_int = std::vector<std::vector<int>>;

    Matrix_double r(num_test, std::vector<double>(num_mbonos));
    Matrix_double P(num_test, std::vector<double>(num_mbonos));
    Matrix_double TC(num_test, std::vector<double>(num_mbonos));
    Matrix_int K(num_test, std::vector<int>(num_mbonos));
    Matrix_int d(num_test, std::vector<int>(num_mbonos));
    Matrix_int dtms(num_test, std::vector<int>(num_mbonos));

    // generate random input prices
    for (int i = 0; i < num_test; i++){
        // generate data required to produce input prices
        for (int j = 0; j < num_mbonos; j++){
            TC[i][j] = TCs[dist_TC(gen)];
            dtms[i][j] = dist_dtm(gen);
            r[i][j] = dist_r(gen);
            K[i][j] = dist_K(gen);
        }

        d[i] = PriceToYield::find_d(dtms[i]);
        K[i] = PriceToYield::find_k(dtms[i]);

        // calculate theoretical price given generated data
        std::vector<double> p = PriceToYield::round_to_vec(px_vec(TC[i], r[i], K[i], d[i]),6);

        // add noise to theoretical price
        std::vector<double> p_err(p.size());
        for (int i = 0; i < p.size();i++){
            p_err[i] = p[i] + pow(-1, dist_pm(gen))*dist_m(gen);
        }
        
        // final input price with noise
        P[i] = PriceToYield::round_to_vec(p_err,6);
    }   

    //test price_to_yield
    double diff = 0; double max_diff = 0; double av_diff = 0;
    double av_time = 0; 
    int failures = 0; double failure_pct = 0;
    std::vector<double> P_result;
    std::vector<double> P_expected;
    Matrix_double yields(num_test, std::vector<double>(num_mbonos));

    auto start = high_resolution_clock::now();
    for (int i = 0; i < num_test; i++){
        // calculate yields associated with generated prices
        yields[i] = PriceToYield::price_to_yield(
            P[i], dtms[i], TC[i]
        );

        // input yield result to px to compute theoretical prices and round
        P_result = PriceToYield::round_to_vec(px_vec(TC[i], yields[i],
        K[i], d[i]),6);
        P_expected = P[i];
       
        // check computed prices equal to generated prices

        for (int j = 0; j<num_mbonos; j++){
            if(P_result[j] != P_expected[j]){
                failures++;
                diff += P_result[j] - P_expected[j];
                max_diff = std::max(P_result[j] - P_expected[j], max_diff);
            }
            EXPECT_EQ(P_result[j], P_expected[j])
            << "\n"
            << "Failed case " << i << "\n"
            << "*********************************" << "\n"
            << " | Input Price = " << P[i][j] << "\n"
            << " | TC = " << TC[i][j] << "\n"
            << " | DTM = " << dtms[i][j] << "\n"
            << " | r true = " << r[i][j] << "\n"
            << " | r found = " << yields[i][j] << "\n"
            << " | P expected = " << P_expected[j] << "\n"
            << " | P result = " << P_result[j] << "\n"
            << " | diff = " << std::abs(P_result[j] - P_expected[j]) <<"\n"
            << "*********************************"
            << "\n";

        }
        
        
    }
    auto end = high_resolution_clock::now();

    // performance metrics
    av_time = static_cast<double>(duration_cast<microseconds>(end - start).count()) / 1000.0/(num_test*num_mbonos);
    av_diff = diff/num_test;
    failure_pct = 100.0 * failures / num_test;

    std::cout << "\n"
              << "SUMMARY"
              << " | Tests: " << num_test << " (" << num_test*num_mbonos << " bonds)" << "\n"
              << "==========================================" <<"\n"
              << " | Avg diff: " << av_diff
              << " | Max diff: " << max_diff << "\n"
              << " | Avg time: " << av_time << " ms" <<"\n"
              << "==========================================" <<"\n"
              << " Fail count: "<< failures 
              << " | Failure rate: " << failure_pct << "%" 
              << "\n" << "\n";
}

double px(double TC, double r, int K, int d){
    const double R = 0.01*r*DPP/YB;
    const double C = VN*(DPP*0.01*TC)/YB;
    const double price = (C + C * (1 / R - 1 / (R * pow(1 + R, K - 1)))
                + VN / pow(1 + R, K - 1))/ pow(1 + R, 1 - 1.0*d / DPP)
                - C * 1.0*d / DPP;

    return price;
}

std::vector<double> px_vec(std::vector<double> TC_vec,
                           std::vector<double> r_vec,
                           std::vector<int> K_vec,
                           std::vector<int>  d_vec){
         
    std::vector<double> px_vec(TC_vec.size()); 

    for (int i = 0; i<TC_vec.size();i++){
        const double R = 0.01*r_vec[i]*DPP/YB;
        const double C = VN*(DPP*0.01*TC_vec[i])/YB;
        const int K = K_vec[i];
        const int d = d_vec[i];
        px_vec[i] = (C + C * (1 / R - 1 / (R * pow(1 + R, K - 1)))
                + VN / pow(1 + R, K - 1))/ pow(1 + R, 1 - 1.0*d / DPP)
                - C * 1.0*d / DPP;
    }
    return px_vec;
}



double round_to(double num, int dp){

    double factor = std::pow(10, dp);
  
    return std::round(num * factor) / factor;
}

