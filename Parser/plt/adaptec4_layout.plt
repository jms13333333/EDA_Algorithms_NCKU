set terminal pngcairo size 800,600 enhanced font 'Arial,10'
set output 'adaptec4_layout.png'
set title 'adaptec4 Layout'
set xlabel 'X'
set ylabel 'Y'
set size ratio -1
set grid
plot '_chip.dat' using 1:2 with lines title 'Chip', \
     '_pad.dat' using 1:2:3:4 with vectors title 'Pads'
