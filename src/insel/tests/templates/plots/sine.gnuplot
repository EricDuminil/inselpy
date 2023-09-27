set macro
set style data lines
thin  = "1"
thick = "2"
set style line 1 linecolor rgbcolor "#f2880a" linewidth @thick
set style line 2 linecolor rgbcolor "#f2880a" linewidth @thin
set style increment user
set title "Sine test"
set ylabel '$ template_name $ '
set ytics nomirror
set xtics nomirror
set output '$plot_folder$/sine.png'
set terminal pngcairo font 'Calibri, 16' size 1400, 800
plot "$result_folder$/insel.gpl" title "My $ template_name $"
