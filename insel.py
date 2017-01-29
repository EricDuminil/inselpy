class MetaBlock(type):
  #     s 1 CONST
  #     p 1
  #             6
  #     s 2 CONST
  #     p 2
  #             4
  #     s 3 sum 1.1 2.1 
  #     s 4 SCREEN 3.1
  #     p 4
  #             '(6E15.7)'
  def __getattr__(self, name):
    def test():
        print ".."

    def _missing(*args, **kwargs):
        test()
        inputs = []
        for i,arg in enumerate(args, 1):
          inputs.append("%s.1" % i)
          print "s %d CONST" % i
          print "p %d" % i,
          print "\t%r" % arg
          print

        print "s %d %s %s" % (len(args)+1,name.upper(), " ".join(inputs))
        print

        print "s %d SCREEN %d.1" % (len(args)+2, len(args)+1),

        print 
    return _missing

class Block():
  __metaclass__ = MetaBlock
