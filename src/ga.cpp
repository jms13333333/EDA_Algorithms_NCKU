// ga.cpp
#include "ga.h"
#include "placer.h"

#include <algorithm>
#include <iostream>
#include <chrono>
#include <unordered_map>

GeneticAlgorithm::GeneticAlgorithm(Circuit& circuit, Placer& placer)
    : circuit_(circuit), placer_(placer) {
    // 初始化 RNG
    std::random_device rd;
    rng_ = std::mt19937(rd());

    initMacroNames();
}

void GeneticAlgorithm::initMacroNames() {
    macroNames_.clear();
    macroNames_.reserve(circuit_.macros.size());
    for (const auto& kv : circuit_.macros) {
        // 只放 isMacro == true 的元件
        if (kv.second.isMacro) {
            macroNames_.push_back(kv.first);
        }
    }
}

void GeneticAlgorithm::initPopulation() {
    population_.clear();

    if (macroNames_.empty()) {
        std::cerr << "[WARN] No macros in circuit. GA population will be empty.\n";
        return;
    }

    std::uniform_int_distribution<int> orientDist(0, 7); // 8 種方向 (先占位用)

    for (int i = 0; i < populationSize_; ++i) {
        Chromosome c;

        // order: 一開始用 macroNames_，再做隨機打亂
        c.order = macroNames_;
        std::shuffle(c.order.begin(), c.order.end(), rng_);

        // orientations: 每個 macro 一個整數 (目前不真的用，先放 0 或隨機)
        c.orientations.resize(macroNames_.size(), 0);
        for (size_t j = 0; j < c.orientations.size(); ++j) {
            c.orientations[j] = orientDist(rng_);
        }

        c.cost = 1e100;
        population_.push_back(c);
    }
}

void GeneticAlgorithm::evaluatePopulation() {
    for (auto& c : population_) {
        c.cost = evaluateChromosome(c);
    }
}

Chromosome GeneticAlgorithm::tournamentSelect(int k) {
    if (population_.empty()) {
        // 理論上不應該發生，保險起見
        return Chromosome{};
    }

    std::uniform_int_distribution<int> idxDist(0, (int)population_.size() - 1);

    Chromosome best = population_[idxDist(rng_)];
    for (int i = 1; i < k; ++i) {
        Chromosome& challenger = population_[idxDist(rng_)];
        if (challenger.cost < best.cost) {
            best = challenger;
        }
    }
    return best;
}

// 使用 OX (Order Crossover) 產生新的 order，orientations 先簡單混合
Chromosome GeneticAlgorithm::crossover(const Chromosome& p1, const Chromosome& p2) {
    Chromosome child;
    const int n = (int)p1.order.size();
    child.order.resize(n);
    child.orientations.resize(n, 0);
    child.cost = 1e100;

    if (n == 0) return child;

    std::uniform_int_distribution<int> cutDist(0, n - 1);
    int c1 = cutDist(rng_);
    int c2 = cutDist(rng_);
    if (c1 > c2) std::swap(c1, c2);

    // 1. 先把 [c1, c2] 區間從 p1 複製到 child
    std::unordered_map<std::string, bool> used;
    for (int i = c1; i <= c2; ++i) {
        child.order[i] = p1.order[i];
        used[p1.order[i]] = true;
    }

    // 2. 從 p2 開始，依序填補 child 中其餘位置
    int idx = (c2 + 1) % n;
    int p2idx = (c2 + 1) % n;
    while (idx != c1) {
        const std::string& candidate = p2.order[p2idx];
        if (!used[candidate]) {
            child.order[idx] = candidate;
            used[candidate] = true;
            idx = (idx + 1) % n;
        }
        p2idx = (p2idx + 1) % n;
    }

    // 3. orientations 就簡單從 p1 or p2 拿 (先不講究)
    for (int i = 0; i < n; ++i) {
        // 找到 child.order[i] 在 p1.order 裡面的 index
        auto it = std::find(p1.order.begin(), p1.order.end(), child.order[i]);
        if (it != p1.order.end()) {
            int pos = (int)std::distance(p1.order.begin(), it);
            child.orientations[i] = p1.orientations[pos];
        }
    }

    return child;
}

void GeneticAlgorithm::mutate(Chromosome& c) {
    const int n = (int)c.order.size();
    if (n <= 1) return;

    std::uniform_real_distribution<double> prob(0.0, 1.0);
    std::uniform_int_distribution<int> idxDist(0, n - 1);

    // 簡單版本：隨機 swap 兩個 macro
    if (prob(rng_) < 0.8) {
        int i = idxDist(rng_);
        int j = idxDist(rng_);
        if (i != j) std::swap(c.order[i], c.order[j]);
    }

    // orientations 隨機改一下
    int k = idxDist(rng_);
    c.orientations[k] = (c.orientations[k] + 1) % 8;
}

double GeneticAlgorithm::evaluateChromosome(Chromosome& c) {
    // 如果沒有 macro，cost = 超大
    if (macroNames_.empty()) {
        return 1e100;
    }

    // 交給 Placer 算 cost (目前 Placer::evaluatePlacement 不會 segfault)
    double cost = placer_.evaluatePlacement(c);
    return cost;
}

Chromosome GeneticAlgorithm::run() {
    Chromosome best;

    if (macroNames_.empty()) {
        std::cerr << "[WARN] No macros in circuit. GA will return empty solution.\n";
        best.cost = 1e100;
        return best;
    }

    initPopulation();
    evaluatePopulation();

    // 初始化 best
    best = population_[0];
    for (const auto& c : population_) {
        if (c.cost < best.cost) best = c;
    }

    std::uniform_real_distribution<double> prob(0.0, 1.0);

    for (int gen = 0; gen < maxGenerations_; ++gen) {
        std::vector<Chromosome> newPop;
        newPop.reserve(populationSize_);

        while ((int)newPop.size() < populationSize_) {
            Chromosome parent1 = tournamentSelect();
            Chromosome parent2 = tournamentSelect();

            Chromosome child1 = parent1;
            Chromosome child2 = parent2;

            if (prob(rng_) < crossoverRate_) {
                child1 = crossover(parent1, parent2);
                child2 = crossover(parent2, parent1);
            }

            if (prob(rng_) < mutationRate_) mutate(child1);
            if (prob(rng_) < mutationRate_) mutate(child2);

            child1.cost = evaluateChromosome(child1);
            child2.cost = evaluateChromosome(child2);

            newPop.push_back(child1);
            if ((int)newPop.size() < populationSize_) {
                newPop.push_back(child2);
            }
        }

        population_ = std::move(newPop);

        // 更新當前最佳
        for (const auto& c : population_) {
            if (c.cost < best.cost) best = c;
        }

        std::cout << "[GA] Gen " << gen << " best cost = " << best.cost << "\n";
    }

    return best;
}
