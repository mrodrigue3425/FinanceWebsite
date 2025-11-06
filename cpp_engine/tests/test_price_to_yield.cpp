#include <gtest/gtest.h>
#include "../price_to_yield.h"

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