// Parser.h
#pragma once

#include <string>
#include "data_structures.h"

class Parser {
public:
    // benchmarkDir 例: "../benchmarks/adaptec1/"
    explicit Parser(const std::string& benchmarkDir);

    // 主入口：設定檔名 → 解析 nodes / pl / nets / scl
    bool parseAll(Circuit& circuit);

    // 個別解析函式（parseAll 會用到）
    bool parseNodes(const std::string& filename, Circuit& circuit);
    bool parsePl(const std::string& filename, Circuit& circuit);
    bool parseNets(const std::string& filename, Circuit& circuit);
    bool parseScl(const std::string& filename);

private:
    std::string benchmarkDir_;

    std::string nodesFile_;
    std::string plFile_;
    std::string netsFile_;
    std::string sclFile_;

    bool parseAux();
};
