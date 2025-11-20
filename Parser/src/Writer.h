#ifndef WRITER_H
#define WRITER_H

#include <string>
#include <fstream>
#include <iostream>

class Writer {
public:
    // 生成晶片 core 區域檔案
    void writeChipDat(const std::string& filename) const {
        std::ofstream out(filename);
        if(!out) {
            std::cerr << "Error: cannot open file " << filename << std::endl;
            return;
        }
        // 範例資料
        out << "# Chip boundary coordinates\n";
        out << "0 0\n";
        out << "100 0\n";
        out << "100 50\n";
        out << "0 50\n";
        out.close();
    }

    // 生成 pad 檔案
    void writePadDat(const std::string& filename) const {
        std::ofstream out(filename);
        if(!out) {
            std::cerr << "Error: cannot open file " << filename << std::endl;
            return;
        }
        // 範例 pad 資料：x y width height direction
        out << "# pad x y w h direction\n";
        out << "0 25 5 5 N\n";
        out << "100 25 5 5 S\n";
        out.close();
    }

    // 生成 pad pin 檔案
    void writePadPinDat(const std::string& filename) const {
        std::ofstream out(filename);
        if(!out) {
            std::cerr << "Error: cannot open file " << filename << std::endl;
            return;
        }
        // 範例 pad pin 資料 (大小固定 3x3)
        out << "# pad pin x y size\n";
        out << "0 25 3\n";
        out << "100 25 3\n";
        out.close();
    }

    // 生成 gnuplot 腳本
    void writeGnuplotScript(const std::string& benchName,
                            const std::string& chipDat,
                            const std::string& padDat) const {
        std::ofstream out(benchName + "_layout.plt");
        if(!out) {
            std::cerr << "Error: cannot open file " << benchName << "_layout.plt" << std::endl;
            return;
        }

        out << "set terminal pngcairo size 800,600 enhanced font 'Arial,10'\n";
        out << "set output '" << benchName << "_layout.png'\n";
        out << "set title '" << benchName << " Layout'\n";
        out << "set xlabel 'X'\nset ylabel 'Y'\n";
        out << "set size ratio -1\n";
        out << "set grid\n";
        out << "plot '" << chipDat << "' using 1:2 with lines title 'Chip', \\\n";
        out << "     '" << padDat << "' using 1:2:3:4 with vectors title 'Pads'\n";

        out.close();
    }
};

#endif // WRITER_H

