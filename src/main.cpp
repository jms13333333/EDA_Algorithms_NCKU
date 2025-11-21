// main.cpp
#include <iostream>
#include <string>

#include "data_structures.h"
#include "Parser.h"
#include "placer.h"
#include "ga.h"

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <case_name>\n";
        std::cerr << "Example: " << argv[0] << " adaptec1\n";
        return 1;
    }

    std::string caseName = argv[1];

    std::string benchmarkDir = "../benchmarks/" + caseName + "/";

    std::cout << "[INFO] Case      : " << caseName << "\n";
    std::cout << "[INFO] Bench dir : " << benchmarkDir << "\n";

    // === 建立 Circuit 結構 ===
    Circuit circuit;
    circuit.name = caseName;

    Parser parser(benchmarkDir);
    if (!parser.parseAll(circuit)) {
        std::cerr << "[ERROR] parseAll() failed. Please check Parser implementation.\n";
        return 1;
    }
    std::cout << "[INFO] Parsing done.\n";

    Placer placer(circuit);
    GeneticAlgorithm ga(circuit, placer);

    std::cout << "[INFO] Start genetic algorithm...\n";
    Chromosome best = ga.run();
    std::cout << "[INFO] GA finished. Best cost = " << best.cost << "\n";

    placer.applyChromosome(best);

    std::string outPath = benchmarkDir + caseName + ".pl_out";
    if (!placer.writePlOut(outPath)) {
        std::cerr << "[ERROR] Failed to write pl_out file: " << outPath << "\n";
        return 1;
    }

    std::cout << "[INFO] Output written to: " << outPath << "\n";
    std::cout << "[INFO] Done.\n";

    return 0;
}
