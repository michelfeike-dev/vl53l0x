#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>

template <std::size_t N> class MedianFilter {
  static_assert(N > 0 && N % 2 == 1, "WINDOW ERROR");

public:
  uint16_t update(uint16_t x) {
    buf_[head_] = x;
    head_ = (head_ + 1) % N;
    if (count_ < N)
      ++count_;

    std::array<uint16_t, N> tmp;
    std::copy_n(buf_.begin(), count_, tmp.begin());
    auto mid = tmp.begin() + count_ / 2;
    std::nth_element(tmp.begin(), mid, tmp.begin() + count_);
    return *mid;
  }

private:
  std::array<uint16_t, N> buf_{};
  std::size_t head_ = 0;
  std::size_t count_ = 0;
};