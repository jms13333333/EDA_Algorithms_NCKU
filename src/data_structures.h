// data_structures.h
#pragma once
#include <string>
#include <vector>
#include <unordered_map>

struct Pin {
    std::string nodeName;
    double xOffset = 0.0;
    double yOffset = 0.0;
};

struct Net {
    std::string name;
    std::vector<Pin> pins;
};

struct Macro {
    std::string name;
    double width = 0.0;
    double height = 0.0;
    bool isFixed = false;
    bool isFixedNI = false;
    bool isMacro = true;

    double x = 0.0; // llx
    double y = 0.0; // lly

    double origX = 0.0;
    double origY = 0.0;
    int orient = 0; // 0~7
};

struct Circuit {
    std::string name;
    std::unordered_map<std::string, Macro> macros;
    std::vector<Net> macroNets;
};
