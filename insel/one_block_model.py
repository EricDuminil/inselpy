import math
from typing import List, Sequence
from .temporary_model import TemporaryModel
from .insel import Parameter


class OneBlockModel(TemporaryModel):
    def __init__(self, name: str = '', inputs: Sequence[float] = None,
                 parameters: List[Parameter] = None, outputs: int = 1):
        super().__init__()
        self.name = name
        self.parameters: List[str] = ["'%s'" % p if isinstance(p, str)
                                      else str(p) for p in parameters]
        self.inputs: Sequence[float] = inputs
        self.n_in: int = len(inputs)
        self.n_out: int = outputs

    def content(self) -> str:
        lines: List[str] = []
        input_ids: List[str] = []
        block_id: int = self.n_in + 1
        screen_id: int = self.n_in + 2

        for i, arg in enumerate(self.inputs, 1):
            input_ids.append("%s.1" % i)
            if math.isnan(arg):
                lines.append("s %d NAN" % i)
            elif math.isinf(arg):
                if arg > 0:
                    lines.append("s %d INFINITY" % i)
                else:
                    lines.append("s %d INFINITY" % (1000 + i))
                    lines.append("s %d CHS %d" % (i, 1000 + i))
            else:
                lines.append("s %d CONST" % i)
                lines.append("p %d" % i)
                lines.append("\t%r" % arg)

        lines.append("s %d %s %s" %
                     (block_id, self.name.upper(), " ".join(input_ids)))
        if self.parameters:
            lines.append("p %d %s" % (block_id, " ".join(self.parameters)))

        lines.append(("s %d SCREEN " % screen_id) +
                     ' '.join("%d.%d" % (block_id, i + 1) for i in range(self.n_out)))

        return "\n".join(lines)
