#include "Writer.h"
#include <fstream>
#include <iostream>

void Writer::writeGnuplotScript(const std::string& benchName,
                                const std::string& chipFile,
                                const std::string& padFile) const
{
    std::ofstream plt("_layout.plt");
    // 產生 gnuplot script
    plt << "set terminal pngcairo size 1200,800\n";
    plt << "set output '_layout.png'\n";
    plt << "set style fill solid 0.5\n";
    plt << "plot '" << chipFile << "' using 1:2:3:4 with box lc rgb 'black' title 'Chip', \\\n";
    plt << "     '" << padFile << "' using 2:3:4:5 with box lc rgb 'red' title 'Pads'\n";
    plt.close();
}

