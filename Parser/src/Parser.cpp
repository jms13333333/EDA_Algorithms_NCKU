#include "Parser.h"
#include <fstream>
#include <sstream>
#include <iostream>

static bool isSkippable(const std::string& line) {
    if (line.empty()) return true;
    for (char c : line) {
        if (c == '#') return true;
        if (!isspace(c)) return false;
    }
    return true;
}

bool Parser::parseAux(const std::string& filename) {
    std::ifstream fin(filename);
    if (!fin) {
        std::cerr << "Error: cannot open aux file " << filename << std::endl;
        return false;
    }

    std::string word;
    while (fin >> word) {
        if (word.find(".nodes") != std::string::npos) parseNodes(word);
        else if (word.find(".nets") != std::string::npos) parseNets(word);
        else if (word.find(".pl") != std::string::npos) parsePl(word);
        else if (word.find(".scl") != std::string::npos) parseScl(word);
    }
    return true;
}

bool Parser::parseNodes(const std::string& filename) {
    std::ifstream fin(filename);
    if (!fin) return false;
    std::string line;
    while (std::getline(fin, line)) {
        if (isSkippable(line)) continue;
        std::stringstream ss(line);
        std::string name, type;
        int w, h;
        ss >> name >> w >> h;
        Node node{name, w, h, false, false};
        if (ss >> type) {
            if (type == "terminal") node.isTerminal = true;
            if (type == "terminal_NI") node.isTerminalNI = true;
        }
        nodes[name] = node;
    }
    return true;
}

bool Parser::parsePl(const std::string& filename) {
    std::ifstream fin(filename);
    if (!fin) return false;
    std::string line;
    while (std::getline(fin, line)) {
        if (isSkippable(line)) continue;
        std::stringstream ss(line);
        Placement plc;
        std::string orientFlag, extra;
        ss >> plc.name >> plc.x >> plc.y >> orientFlag;
        plc.orient = orientFlag[1]; // ":N" → 'N'
        plc.isFixed = false;
        if (ss >> extra) {
            if (extra.find("FIXED") != std::string::npos) plc.isFixed = true;
        }
        placements[plc.name] = plc;
    }
    return true;
}

bool Parser::parseNets(const std::string& filename) {
    std::ifstream fin(filename);
    if (!fin) return false;
    std::string line;
    Net net;
    while (std::getline(fin, line)) {
        if (isSkippable(line)) continue;
        std::stringstream ss(line);
        std::string token;
        ss >> token;
        if (token == "NetDegree") {
            if (!net.name.empty()) { nets.push_back(net); net = Net(); }
            ss >> net.degree >> net.name;
        } else {
            Pin p; p.cellName = token;
            ss >> p.ioType >> p.offsetX >> p.offsetY;
            net.pins.push_back(p);
        }
    }
    if (!net.name.empty()) nets.push_back(net);
    return true;
}

bool Parser::parseScl(const std::string& filename) {
    std::ifstream fin(filename);
    if (!fin) return false;
    std::string line, key;
    Row row;
    while (std::getline(fin, line)) {
        if (isSkippable(line)) continue;
        std::stringstream ss(line);
        ss >> key;
        if (key == "Coordinate") ss >> row.y;
        else if (key == "Height") ss >> row.height;
        else if (key == "Sitewidth") ss >> row.siteWidth;
        else if (key == "Sitespacing") ss >> row.siteSpacing;
        else if (key == "SubrowOrigin") {
            ss >> row.subRowOrigin >> key >> row.numSites;
            rows.push_back(row);
        }
    }
    return true;
}

