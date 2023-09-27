import math
from typing import List, Sequence
from .temporary_model import TemporaryModel
from .insel import Parameter


class OneBlockModel(TemporaryModel):
    """This model is used to calculate the output of one specific block.

    In order to get the block's output, the inputs need to be defined as constants,
    and a SCREEN block needs to display the output.

    The inputs might be floats, infinity or NaN.

    By default, only one output is shown.
    """
    def __init__(self, name: str = '', inputs: Sequence[float] = None,
                 parameters: List[Parameter] = None, outputs: int = 1):
        super().__init__()
        self.name = name
        self.parameters: List[str] = [f"'{p!s}'" if isinstance(p, str)
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
            input_ids.append(f"{i:d}.1")
            if math.isnan(arg):
                lines.append(f"s {i:d} NAN")
            elif math.isinf(arg):
                if arg > 0:
                    lines.append(f"s {i:d} INFINITY")
                else:
                    lines.append(f"s {1000 + i:d} INFINITY")
                    lines.append(f"s {i:d} CHS {1000 + i:d}")
            else:
                lines.append(f"s {i:d} CONST")
                lines.append(f"p {i:d}")
                lines.append(f"\t{arg!r}")

        lines.append(f"s {block_id:d} {self.name.upper()} {' '.join(input_ids)}")
        if self.parameters:
            lines.append(f"p {block_id:d} {' '.join(self.parameters)}")

        screen_inputs = ' '.join(f"{block_id:d}.{i + 1:d}" for i in range(self.n_out))
        lines.append(f"s {screen_id:d} SCREEN {screen_inputs}")

        return "\n".join(lines)
