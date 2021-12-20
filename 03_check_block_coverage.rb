# Quick and dirty script to check how many blocks are tested (green) or present in examples (blue)
# TODO: Check Java classes too
# TODO: Check Java Palette
# TODO: Check Documentation too
COLUMNS = 13
templates = Dir.glob("templates/*.insel")
blocks_in_templates = templates.map{ |t|
  File.read(t).force_encoding("utf-8").encode("utf-8", invalid: :replace, replace: "?").scan(/^[bs]\s+\d+\s+(\w+)/i)
}

blocks_in_py = File.read('02_test_insel.py').scan(/insel\.block\(["'](\w+?)["']/)

tested_blocks = (blocks_in_templates + blocks_in_py).flatten.uniq.sort.map(&:upcase)

all_blocks = `insel -b`.split("\n\n").last.split.sort

examples = Dir.glob("/usr/local/insel/examples/**/*").select{ |f| f =~ /\.(insel|vseit)$/i }
blocks_in_examples = examples.map{ |t|
  File.read(t).force_encoding("utf-8").encode("utf-8", invalid: :replace, replace: "?").scan(/^[bs]\s+\d+\s+(\w+)/i)
}.flatten.uniq.sort

puts "Tested blocks = #{tested_blocks.size} / #{all_blocks.size}"
puts "Example blocks = #{blocks_in_examples.size} / #{all_blocks.size}"
class String
  def colorize(color_code)
    "\e[#{color_code}m#{self}\e[0m"
  end

  def red
    colorize(31)
  end

  def green
    colorize(32)
  end

  def blue
    colorize(34)
  end
end

require 'set'
tested_blocks = Set.new(tested_blocks)
blocks_in_examples = Set.new(blocks_in_examples)

color_blocks = all_blocks.map do |block|
  if tested_blocks.include? block
    block.green
  elsif blocks_in_examples.include? block
    block.blue
  else
    block.red
  end
end

n = color_blocks.size
h = (n / COLUMNS).ceil

rectangle = color_blocks.each_slice(h).map{|l| l + [""] * (h - l.size)}

rectangle = rectangle.map{ |col| max_size = col.map(&:size).max + 2; col.map{ |b| b.ljust(max_size, ' ')} }

rectangle.transpose.each do |bs|
  puts bs.join
end
