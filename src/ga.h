// ga.h
#pragma once

#include <vector>
#include <string>
#include <random>
#include "data_structures.h"

class Placer;  // 前向宣告，避免 circular include

struct Chromosome {
    std::vector<std::string> order;      // macro 放置順序 (名字)
    std::vector<int> orientations;       // 每個 macro 的方向 (先用 0..7 或全 0)
    double cost = 1e100;                 // 越小越好
};

class GeneticAlgorithm {
public:
    GeneticAlgorithm(Circuit& circuit, Placer& placer);

    // 主流程：跑 GA，回傳最佳解
    Chromosome run();

private:
    Circuit& circuit_;
    Placer& placer_;
    std::mt19937 rng_;

    std::vector<std::string> macroNames_;  // 把 circuit.macros 的 key 收成 vector

    std::vector<Chromosome> population_;
    int populationSize_   = 30;
    int maxGenerations_   = 50;
    double crossoverRate_ = 0.8;
    double mutationRate_  = 0.2;

    void initMacroNames();
    void initPopulation();
    void evaluatePopulation();

    Chromosome tournamentSelect(int k = 3);
    Chromosome crossover(const Chromosome& p1, const Chromosome& p2);
    void mutate(Chromosome& c);

    double evaluateChromosome(Chromosome& c);
};
