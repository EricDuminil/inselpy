set macro
set style data lines
thin  = "1"
thick = "2"
set linetype 1 linecolor rgbcolor "#f2880a" linewidth @thick
set linetype 2 linecolor rgbcolor "#f2880a" linewidth @thin
# set style increment user
set title "Sine test"
set ylabel '$ template_name $ '
set ytics nomirror
set xtics nomirror

set xtics 90
set mxtics 3
set format x "%g°"

set output '$plot_folder$/sine.png'
set terminal pngcairo size 1400, 800
# NOTE: Multiple plot blocks can be used. Which means the PLOT block id is included in the filename:
plot "$result_folder$/insel3.gpl" title "My $ template_name $"
