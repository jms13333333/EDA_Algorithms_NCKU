#pragma once
#include <string>
#include <vector>
#include <unordered_map>

struct Node{
    std::string name;
    int width,height;
    bool isTerminal, isTerminalNI;
};

struct Pin{
    std::string cellName;
    char ioType;
    double offsetX, offsetY;
};

struct Net{
    std::string name;
    int degree;
    std::vector<Pin> pins;
};

struct Placement{
    std::string name;
    double x,y;
    char orient;
    bool isFixed;
};

struct Row{
    int y,height;
    int siteWidth, siteSpacing;
    int subRowOrigin, numSites;
};

class Parser{
public:
	bool parseAux(const std::string& filename);
	bool parseNodes(const std::string& filename);
	bool parseNets(const std::string& filename);
	bool parsePl(const std::string& filename);
	bool parseScl(const std::string& filename);

	std::unordered_map<std::string, Node> nodes;
	std::unordered_map<std::string, Placement> placements;
	std::vector<Net> nets;
	std::vector<Row> rows;
};
