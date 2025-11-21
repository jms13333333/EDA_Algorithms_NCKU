// placer.h
#pragma once

#include <string>
#include "data_structures.h"
#include "ga.h"

class Placer {
public:
    explicit Placer(Circuit& circuit);

    // 評估一個 chromosome 的擺置，回傳 HPWL
    double evaluatePlacement(Chromosome& c);

    // 把 best chromosome 的結果真正寫回 circuit.macros
    void applyChromosome(const Chromosome& c);

    // 輸出 pl_out 檔
    bool writePlOut(const std::string& outputPath) const;

    //用原始 pl 的座標計算一次 HPWL
    double evaluateOriginal();

private:
    Circuit& circuit_;

    void resetPlacement();
    void placeMacroSequence(const Chromosome& c);
    void placeSingleMacro(const std::string& name, int orient);
    double computeHPWL() const;
};
