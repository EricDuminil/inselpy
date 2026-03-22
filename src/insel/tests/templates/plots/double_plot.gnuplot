set terminal dumb 100, 40
set output '$plot_folder$/sorted_sine_and_cosine.txt'
set xtics 90
set mxtics 3

set key bottom left

plot "$result_folder$/insel.gpl" title "Sorted sine",\
     "$result_folder$/insel2.gpl" title "Cosine"
