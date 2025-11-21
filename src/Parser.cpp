// Parser.cpp
#include "Parser.h"

#include <fstream>
#include <sstream>
#include <iostream>
#include <cctype>
#include <vector>
#include <algorithm>
#include <unordered_set>

// ===== 小工具 =====

static std::string trim(const std::string& s) {
    size_t b = 0, e = s.size();
    while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;
    return s.substr(b, e - b);
}

static std::vector<std::string> splitTokens(const std::string& line) {
    std::vector<std::string> tokens;
    std::istringstream iss(line);
    std::string tok;
    while (iss >> tok) tokens.push_back(tok);
    return tokens;
}

// ===== Parser 成員實作 =====

Parser::Parser(const std::string& benchmarkDir)
    : benchmarkDir_(benchmarkDir) {
    // 確保 benchmarkDir_ 以 '/' 結尾
    if (!benchmarkDir_.empty() &&
        benchmarkDir_.back() != '/' &&
        benchmarkDir_.back() != '\\') {
        benchmarkDir_ += "/";
    }
}

bool Parser::parseAll(Circuit& circuit) {
    if (!parseAux()) {
        std::cerr << "[ERROR] parseAux() failed.\n";
        return false;
    }

    std::string nodesPath = benchmarkDir_ + nodesFile_;
    std::string plPath    = benchmarkDir_ + plFile_;
    std::string netsPath  = benchmarkDir_ + netsFile_;
    std::string sclPath   = benchmarkDir_ + sclFile_;

    std::cout << "[INFO] nodes : " << nodesPath << "\n";
    std::cout << "[INFO] pl    : " << plPath    << "\n";
    std::cout << "[INFO] nets  : " << netsPath  << "\n";
    std::cout << "[INFO] scl   : " << sclPath   << "\n";

    if (!parseNodes(nodesPath, circuit)) return false;
    if (!parsePl(plPath, circuit))       return false;
    if (!parseNets(netsPath, circuit))   return false;
    if (!parseScl(sclPath))              return false;

    return true;
}

// 不讀 .aux，只用資料夾名稱推 caseName → 檔名
bool Parser::parseAux() {
    std::string dir = benchmarkDir_;
    if (!dir.empty() && (dir.back() == '/' || dir.back() == '\\')) {
        dir.pop_back();
    }

    std::string caseName;
    size_t pos = dir.find_last_of("/\\");
    if (pos == std::string::npos) caseName = dir;
    else caseName = dir.substr(pos + 1);

    nodesFile_ = caseName + ".nodes";
    plFile_    = caseName + ".pl";
    netsFile_  = caseName + ".nets";
    sclFile_   = caseName + ".scl";

    std::cout << "[INFO] (parseAux) caseName  = " << caseName  << "\n";
    std::cout << "[INFO] (parseAux) nodesFile = " << nodesFile_ << "\n";
    std::cout << "[INFO] (parseAux) plFile    = " << plFile_    << "\n";
    std::cout << "[INFO] (parseAux) netsFile  = " << netsFile_  << "\n";
    std::cout << "[INFO] (parseAux) sclFile   = " << sclFile_   << "\n";

    return true;
}

// ===== 只挑最大的 K 個 macro + terminals 當 macro =====

bool Parser::parseNodes(const std::string& filename, Circuit& circuit) {
    std::ifstream fin(filename);
    if (!fin) {
        std::cerr << "[ERROR] Cannot open nodes file: " << filename << "\n";
        return false;
    }

    struct RawNode {
        std::string name;
        double w = 0.0;
        double h = 0.0;
        std::string movetype;   // "", "terminal", "terminal_NI"
        double area = 0.0;
    };

    std::vector<RawNode> allNodes;
    allNodes.reserve(10000);

    std::string line;
    while (std::getline(fin, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;

        if (line.rfind("NumNodes", 0) == 0)     continue;
        if (line.rfind("NumTerminals", 0) == 0) continue;

        std::istringstream iss(line);
        RawNode rn;
        if (!(iss >> rn.name >> rn.w >> rn.h)) continue;
        if (!(iss >> rn.movetype)) {
            rn.movetype = "";
        }
        rn.area = rn.w * rn.h;
        allNodes.push_back(rn);
    }

    if (allNodes.empty()) {
        std::cerr << "[WARN] nodes file has no nodes.\n";
        return true;
    }

    std::sort(allNodes.begin(), allNodes.end(),
              [](const RawNode& a, const RawNode& b) {
                  return a.area > b.area;
              });

    int K = 200; // 先選最大的 200 顆當 macro，之後你可以調
    if (K > (int)allNodes.size()) K = (int)allNodes.size();

    std::unordered_set<std::string> macroSet;
    macroSet.reserve(K * 2);

    for (int i = 0; i < K; ++i) {
        macroSet.insert(allNodes[i].name);
    }
    // 所有 terminal / terminal_NI 也當 macro（IO）
    for (const auto& rn : allNodes) {
        if (rn.movetype == "terminal" || rn.movetype == "terminal_NI") {
            macroSet.insert(rn.name);
        }
    }

    double maxArea = allNodes.front().area;
    std::cout << "[INFO] node_area_max = " << maxArea
              << ", macro_count = " << macroSet.size() << "\n";

    for (const auto& rn : allNodes) {
        Macro m;
        m.name   = rn.name;
        m.width  = rn.w;
        m.height = rn.h;
        m.x      = 0.0;
        m.y      = 0.0;
        m.origX  = 0.0;
        m.origY  = 0.0;
        m.orient = 0;
        m.isFixed   = false;
        m.isFixedNI = false;

        m.isMacro = (macroSet.find(rn.name) != macroSet.end());

        circuit.macros[m.name] = m;
    }

    return true;
}

// ===== parsePl：讀原始 pl 座標，填 x / y / origX / origY =====

bool Parser::parsePl(const std::string& filename, Circuit& circuit) {
    std::ifstream fin(filename);
    if (!fin) {
        std::cerr << "[ERROR] Cannot open pl file: " << filename << "\n";
        return false;
    }

    std::string line;
    while (std::getline(fin, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;
        if (line.rfind("UCLA", 0) == 0) continue;

        std::istringstream iss(line);
        std::string name;
        double x, y;
        std::string colon;
        std::string orient;
        std::string movetype;

        if (!(iss >> name >> x >> y)) continue;
        if (!(iss >> colon)) colon = ":";
        if (!(iss >> orient)) orient = "N";
        iss >> movetype; // 可能是 /FIXED 或 /FIXED_NI 或空

        auto it = circuit.macros.find(name);
        if (it == circuit.macros.end()) {
            // pl 可能有 cell，我們 nodes 裡未必有 → 略過
            continue;
        }

        Macro& m = it->second;
        m.x     = x;
        m.y     = y;
        m.origX = x;
        m.origY = y;

        if (movetype == "/FIXED") {
            m.isFixed = true;
        } else if (movetype == "/FIXED_NI") {
            m.isFixedNI = true;
        }
    }

    return true;
}

// ===== parseNets：建 macroNets（net 本身不強制只含 macro，HPWL 時會過濾）=====

bool Parser::parseNets(const std::string& filename, Circuit& circuit) {
    std::ifstream fin(filename);
    if (!fin) {
        std::cerr << "[ERROR] Cannot open nets file: " << filename << "\n";
        return false;
    }

    std::string line;
    int pinsLeft = 0;
    Net curNet;

    while (std::getline(fin, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;

        if (line.rfind("NumNets", 0) == 0) continue;
        if (line.rfind("NumPins", 0) == 0) continue;

        if (line.rfind("NetDegree", 0) == 0) {
            if (pinsLeft == 0 && !curNet.pins.empty()) {
                circuit.macroNets.push_back(curNet);
                curNet = Net();
            }

            auto tokens = splitTokens(line);
            if (tokens.size() >= 3) {
                pinsLeft = std::stoi(tokens[2]);
            }
            if (tokens.size() >= 4) {
                curNet.name = tokens[3];
            } else {
                curNet.name = "";
            }
            curNet.pins.clear();
            continue;
        }

        if (pinsLeft > 0) {
            std::istringstream iss(line);
            std::string nodeName;
            std::string dir;
            std::string colon;
            double dx = 0.0, dy = 0.0;

            if (!(iss >> nodeName >> dir)) continue;
            iss >> colon;
            iss >> dx >> dy;

            Pin p;
            p.nodeName = nodeName;
            p.xOffset  = dx;
            p.yOffset  = dy;
            curNet.pins.push_back(p);

            --pinsLeft;
            if (pinsLeft == 0) {
                circuit.macroNets.push_back(curNet);
                curNet = Net();
            }
        }
    }

    return true;
}

bool Parser::parseScl(const std::string& filename) {
    std::ifstream fin(filename);
    if (!fin) {
        std::cerr << "[ERROR] Cannot open scl file: " << filename << "\n";
        return false;
    }
    // 之後若要用 row 資訊再補
    return true;
}
