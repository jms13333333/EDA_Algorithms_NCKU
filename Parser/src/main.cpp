#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <sys/stat.h>
#include <cstdlib>
#include <limits.h>
#include <unistd.h>
#include "Writer.h"   // Writer 類負責生成檔案

bool fileExists(const std::string& filename) {
    struct stat buffer;
    return (stat(filename.c_str(), &buffer) == 0);
}

std::string getAbsolutePath(const std::string& path) {
    char absPath[PATH_MAX];
    if(realpath(path.c_str(), absPath) != nullptr) {
        return std::string(absPath);
    } else {
        return path;
    }
}

int main(int argc, char* argv[]) {
    if(argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <benchmark.aux>" << std::endl;
        return 1;
    }

    std::string auxFile = argv[1];
    std::string auxFullPath = getAbsolutePath(auxFile);

    if(!fileExists(auxFile)) {
        std::cerr << "Error: Cannot find aux file: " << auxFile 
                  << " (absolute path: " << auxFullPath << ")" << std::endl;
        return 1;
    }

    std::ifstream fin(auxFile);
    if(!fin) {
        std::cerr << "Error: Cannot open aux file: " << auxFile 
                  << " (absolute path: " << auxFullPath << ")" << std::endl;
        return 1;
    }

    std::cout << "Successfully opened aux file: " << auxFullPath << std::endl;

    // 解析 aux 檔案裡的其他檔案
    std::string nodesFile, plFile, sclFile, netsFile;
    std::string line;
    while(std::getline(fin, line)) {
        if(line.empty() || line[0]=='#') continue;
        std::istringstream iss(line);
        std::string key;
        if(!(iss >> key)) continue;
        if(key == "RowBasedPlacement:") {
            if(!(iss >> nodesFile >> netsFile >> plFile >> sclFile)) continue;
        }
    }
    fin.close();

    std::string files[] = {nodesFile, plFile, sclFile, netsFile};
    for(const auto& f : files) {
        if(!f.empty()) {
            std::string fullPath = getAbsolutePath(f);
            if(!fileExists(f)) {
                std::cerr << "Error: Required file not found: " << f 
                          << " (absolute path: " << fullPath << ")" << std::endl;
                return 1;
            } else {
                std::cout << "Found file: " << fullPath << std::endl;
            }
        }
    }

    std::cout << "All required benchmark files exist. Generating output files..." << std::endl;

    // 呼叫 Writer 產生輸出檔
    Writer writer;
    writer.writeChipDat("_chip.dat");
    writer.writePadDat("_pad.dat");
    writer.writePadPinDat("_pad_pin.dat");
    
    writer.writeGnuplotScript("bigblue4", "_chip.dat", "_pad.dat");

    std::cout << "Generated _chip.dat, _pad.dat, _pad_pin.dat, _layout.plt" << std::endl;

    return 0;
}
 
                        
