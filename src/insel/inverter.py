import math
from dataclasses import dataclass, field
from pathlib import Path

import insel

_TEMPLATES_DIR = Path(__file__).resolve().parent / "tests" / "templates" / "inverter"


@dataclass
class EtaCurve:
    """Computes INSEL inverter loss parameters from efficiency specifications.

    The three parameters model the losses of the IVP block:
    * p_self  — normalized constant self-consumption
    * v_loss  — normalized linear (voltage) losses
    * r_loss  — normalized quadratic (ohmic) losses

    >>> p_self, v_loss, r_loss = EtaCurve.find_params(pm=0.50, em=0.982, ee=0.979)
    """

    pm: float  # power fraction at which eta_max is achieved
    eta_max: float  # peak efficiency
    desired_eta_euro: float

    @classmethod
    def find_params(cls, pm: float, em: float, ee: float) -> list:
        """Iteratively fit (p_self, v_loss, r_loss) from efficiency specs.

        pm -- power fraction at which maximum efficiency is achieved
        em -- maximum efficiency
        ee -- Euro efficiency (weighted average over partial loads)

        Returns [p_self, v_loss, r_loss] for use as IVP block parameters.
        """
        c = (1 - em) / (2 * em * pm)
        ec = cls(pm, em, ee)
        for _ in range(20):
            c = (em - ee) / (em - ec.eta_euro(c)) * c
        return [ec.a(c), ec.b(c), c]

    def a(self, c: float) -> float:
        return self.pm**2 * c

    def b(self, c: float) -> float:
        return (self.pm - self.eta_max * (self.pm + 2 * self.a(c))) / (
            self.pm * self.eta_max
        )

    def eta(self, i: float, c: float) -> float:
        return -(1 + self.b(c)) / (2 * c * i) + math.sqrt(
            (1 + self.b(c)) ** 2 / (2 * c * i) ** 2 + (i - self.a(c)) / (c * i**2)
        )

    def eta_euro(self, c: float) -> float:
        """Weighted average efficiency using the Euro standard weighting."""
        return (
            0.03 * self.eta(0.05, c)
            + 0.06 * self.eta(0.10, c)
            + 0.13 * self.eta(0.20, c)
            + 0.10 * self.eta(0.30, c)
            + 0.48 * self.eta(0.50, c)
            + 0.20 * self.eta(1.0, c)
        )


@dataclass
class Inverter:
    """Derives INSEL IVP block parameters for a grid-tied inverter from its efficiency specs.

    On instantiation, iteratively fits three normalized loss parameters that reproduce
    the specified eta_max and eta_euro when used with the INSEL IVP block:

    * params['p_self']        — normalized self-consumption (constant losses)
    * params['v_loss']        — normalized voltage losses (linear)
    * params['r_loss']        — normalized ohmic losses (quadratic)
    * params['nominal_power'] — nominal AC power [W]

    The correction step accounts for the slight dependence of the peak-efficiency
    power point on the loss parameters themselves.

    >>> inv = Inverter("Fronius", "Symo 10k",
    ...                nominal_power=10000, p_for_eta_max=0.50,
    ...                eta_max=0.982, eta_euro=0.979, inverter_id="f100")
    >>> abs(inv.simulated_eta_euro - inv.eta_euro) < 0.002
    True
    """

    manufacturer_name: str
    name: str
    nominal_power: float
    eta_max: float
    eta_euro: float
    p_for_eta_max: float = 0.40
    inverter_id: str = ""
    output_folder: Path = field(default_factory=lambda: Path.cwd() / "output")

    _OK = "dark_cyan"
    _WARNING = "dark_orange"

    def __post_init__(self):
        if not self.inverter_id:
            nominal_power = self.nominal_power
            if nominal_power >= 1000:
                nominal_power /= 1000
            self.inverter_id = f"{self.name[0].lower()}{int(nominal_power)}"
        self.output_folder = Path(self.output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.params = self._find_corrected_params()
        self.params["nominal_power"] = self.nominal_power

    def __str__(self) -> str:
        return f"{self.manufacturer_name} {self.name} ({self.nominal_power} W)"

    @property
    def simulated_p_for_eta_max(self) -> float:
        """Power fraction at which simulated efficiency peaks."""
        return insel.template(
            _TEMPLATES_DIR / "p_for_eta_max",
            run_in_templates_folder=False,
            **self.params,
        )

    @property
    def simulated_eta_max(self) -> float:
        """Peak efficiency from INSEL simulation."""
        return insel.template(
            _TEMPLATES_DIR / "eta_max",
            run_in_templates_folder=False,
            **self.params,
        )

    @property
    def simulated_eta_euro(self) -> float:
        """Euro efficiency computed via INSEL IVP block and IVETAEU."""
        powers = insel.template(
            _TEMPLATES_DIR / "inverter_etas",
            run_in_templates_folder=False,
            **self.params,
        )
        return insel.block("IVETAEU", parameters=powers)

    @property
    def simulated_eta_cec(self) -> float:
        """CEC efficiency (Sandia weighting) from INSEL simulation."""
        eta_10, eta_20, eta_30, eta_50, eta_75, eta_100 = insel.template(
            _TEMPLATES_DIR / "inverter_cec_etas",
            run_in_templates_folder=False,
            **self.params,
        )
        return (
            eta_10 * 0.04
            + eta_20 * 0.05
            + eta_30 * 0.12
            + eta_50 * 0.21
            + eta_75 * 0.53
            + eta_100 * 0.05
        )

    def plot(
        self, width: int = 100, height: int = 40, plots_folder: Path = Path("plots")
    ) -> Path:
        """Render the η(DC) efficiency curve to a text file. Requires gnuplot.

        Returns the path of the generated text file.
        """
        plots_folder = Path(plots_folder)
        plots_folder.mkdir(exist_ok=True, parents=True)
        insel.plot(
            _TEMPLATES_DIR / "inverter_eta_curve_text",
            manufacturer_name=self.manufacturer_name,
            name=self.name,
            iv_id=self.inverter_id,
            width=width,
            height=height,
            plots_folder=plots_folder,
            **self.params,
        )
        return plots_folder / f"inverter_eta_curve_{self.inverter_id}.txt"

    def report(self):
        """Print a comparison table of specified vs. simulated efficiency values."""
        compare = [
            (
                "% of power at which η_max is achieved",
                self.p_for_eta_max * 100,
                self.simulated_p_for_eta_max * 100,
                "%",
            ),
            ("η_max", self.eta_max * 100, self.simulated_eta_max * 100, "%"),
            ("η_euro", self.eta_euro * 100, self.simulated_eta_euro * 100, "%"),
        ]
        try:
            from rich import box
            from rich.console import Console
            from rich.table import Table

            table = Table(title=" ".join([self.manufacturer_name, self.name]))
            table.add_column("Value", justify="left", no_wrap=True)
            table.add_column("Simulated", justify="right")
            table.add_column("Unit", justify="left")
            table.add_column("Deviation", justify="center")
            for row_name, original, simulated, unit in compare:
                percent = (simulated - original) / original * 100
                color = self._OK if abs(percent) < 2.0 else self._WARNING
                table.add_row(
                    row_name, f"{simulated:.1f}", unit, f"{percent:+.2f} %", style=color
                )
            table.add_row(
                "η_CEC", f"{self.simulated_eta_cec * 100:.1f}", "%", style=self._OK
            )
            table.add_row(
                "Normalized self-consumption",
                f"{self.params['p_self']:.7f}",
                style=self._OK,
            )
            table.add_row(
                "Normalized voltage losses",
                f"{self.params['v_loss']:.7f}",
                style=self._OK,
            )
            table.add_row(
                "Normalized ohmic losses",
                f"{self.params['r_loss']:.7f}",
                style=self._OK,
            )
            table.box = box.MINIMAL
            table.width = 80
            Console().print(table)
        except ImportError:
            print(f"{self.manufacturer_name} {self.name}")
            for row_name, original, simulated, unit in compare:
                percent = (simulated - original) / original * 100
                print(f"  {row_name}: {simulated:.1f} {unit} ({percent:+.2f} %)")
            print(f"  η_CEC: {self.simulated_eta_cec * 100:.1f} %")
        self.write_example_vseit()
        print(
            f"VSEIT example written to {self.output_folder / f'inverter_{self.inverter_id}_example.vseit'}"
        )

    def write_example_vseit(self):
        from .template import Template

        t = Template(
            _TEMPLATES_DIR / "inverter_eta_curve.vseit",
            run_in_templates_folder=False,
            gnuplot=True,
            manufacturer_name=self.manufacturer_name,
            name=self.name,
            p_dc_max=math.ceil(self.nominal_power * 1.2 / 500) * 500,
            **self.params,
        )
        (self.output_folder / f"inverter_{self.inverter_id}_example.vseit").write_text(
            t.content(), encoding="utf-8"
        )

    def _find_params(self, p_max: float) -> dict:
        p_self, v_loss, r_loss = EtaCurve.find_params(
            p_max, self.eta_max, self.eta_euro
        )
        return dict(p_self=p_self, v_loss=v_loss, r_loss=r_loss)

    def _simulated_p_for_eta_max(self, p_max: float) -> float:
        params = self._find_params(p_max)
        return insel.template(
            _TEMPLATES_DIR / "p_for_eta_max",
            run_in_templates_folder=False,
            **params,
        )

    def _corrected_p_for_pmax(self) -> float:
        """Linear interpolation to correct for the bias in EtaCurve.find_params."""
        delta = 0.10
        p_05 = self._simulated_p_for_eta_max(self.p_for_eta_max - delta)
        p_95 = self._simulated_p_for_eta_max(self.p_for_eta_max + delta)
        a = (p_95 - p_05) / (2 * delta)
        b = p_05 - (self.p_for_eta_max - delta) * a
        return (self.p_for_eta_max - b) / a

    def _find_corrected_params(self) -> dict:
        return self._find_params(self._corrected_p_for_pmax())
