import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

import insel

_TEMPLATES_DIR = (
    Path(__file__).resolve().parent / "tests" / "templates" / "photovoltaic"
)


@dataclass
class PhotovoltaicModuleModel:
    """Represents a PV module and derives INSEL simulation parameters via PVDET1.

    On instantiation, runs the PVDET1 block to generate a .bp file in output_folder.
    All subsequent simulation methods (simulated_mpp, simulated_u_oc, etc.) read that
    file, so output_folder must remain writable and stable for the object's lifetime.

    Parameters are validated after PVDET1 runs: sign of alpha coefficients, relative
    ordering of mpp vs. nameplate values, and the power temperature coefficient range.

    >>> module = PhotovoltaicModuleModel(
    ...     manufacturer_name="Acme", name="Sol 250",
    ...     mpp=250, u_oc=37.5, i_sc=8.7, u_mpp=30.5, i_mpp=8.2,
    ...     noct=47, alpha_u_percent=-0.32, alpha_i_percent=0.05,
    ...     rows=6, columns=10, height=1.65, width=0.995, eta=15.3,
    ...     output_folder=Path("/tmp/insel_pv"),
    ... )
    >>> module.simulated_mpp()           # W at STC
    250.x
    >>> module.simulated_u_oc()          # V at STC
    37.x
    """

    manufacturer_name: str
    name: str
    mpp: float
    u_oc: float
    i_sc: float
    u_mpp: float
    i_mpp: float
    noct: float
    alpha_u_percent: float
    alpha_i_percent: float
    rows: int
    columns: int
    height: float
    width: float
    eta: float
    pv_id: str = ""
    parallel: int = 1
    module_tolerance: float = 5.0
    mass: float = 20.0
    module_technology: str = "crystalline_silicon"
    maximum_voltage: float = 1000  # [V]
    absorption_coefficient: float = 0.7
    emission_coefficient: float = 0.85
    specific_module_heat_capacity: float = 900  # [J / (kg * K)]
    output_folder: Path = field(default_factory=lambda: Path.cwd() / "output")

    def __post_init__(self):
        if not self.pv_id:
            self.pv_id = f"{self.name[0].lower()}{int(self.mpp)}"
        self.output_folder = Path(self.output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        insel.OneBlockModel(
            "PVDET1", inputs=[], parameters=self._pvdet1_params(), outputs=6
        ).run()
        self._validate()

    def _validate(self):
        if self.alpha_i < 0:
            raise ValueError("alpha_i must be positive")
        if self.alpha_u > 0:
            raise ValueError("alpha_u must be negative")
        if self.u_mpp >= self.u_oc:
            raise ValueError(
                f"u_mpp ({self.u_mpp}) must be less than u_oc ({self.u_oc})"
            )
        if self.i_mpp >= self.i_sc:
            raise ValueError(
                f"i_mpp ({self.i_mpp}) must be less than i_sc ({self.i_sc})"
            )
        dmpp_dt = self.dmpp_dt
        if not -0.20 >= dmpp_dt >= -0.60:
            raise ValueError(
                f"Power temperature coefficient {dmpp_dt:.2f} % / K is outside [-0.20, -0.60]"
            )

    def report(self):
        """Print a comparison table of nameplate vs. simulated values."""
        compare = [
            ("Pmpp", self.mpp, self.simulated_mpp(), "W"),
            ("Umpp", self.u_mpp, self.simulated_u_mpp(), "V"),
            ("Impp", self.i_mpp, self.simulated_i_mpp(), "A"),
            ("Uoc", self.u_oc, self.simulated_u_oc(), "V"),
            ("Isc", self.i_sc, self.simulated_i_sc(), "A"),
            ("η", self.eta, self.simulated_eta(), "%"),
        ]
        try:
            from rich import box
            from rich.console import Console
            from rich.table import Table

            table = Table(title=f"{self.manufacturer_name}\n{self.name}")
            table.add_column("Value", justify="left", no_wrap=True)
            table.add_column("Simulated", justify="right")
            table.add_column("Unit", justify="left")
            table.add_column("Deviation", justify="center")
            for row_name, original, simulated, unit in compare:
                percent = (simulated - original) / original * 100
                color = "dark_cyan" if abs(percent) < 0.5 else "dark_orange"
                table.add_row(
                    row_name, f"{simulated:.1f}", unit, f"{percent:+.2f} %", style=color
                )
            table.add_row(
                "dMPP / dT", f"{self.dmpp_dt:.2f}", "% / K", style="dark_cyan"
            )
            table.add_row(
                "Fill Factor",
                f"{self.simulated_fill_factor():.1f}",
                "%",
                style="dark_cyan",
            )
            table.box = box.MINIMAL
            table.width = 80
            Console().print(table)
        except ImportError:
            print(f"{self.manufacturer_name} {self.name}")
            for row_name, original, simulated, unit in compare:
                percent = (simulated - original) / original * 100
                print(f"  {row_name}: {simulated:.1f} {unit} ({percent:+.2f} %)")
            print(f"  dMPP / dT: {self.dmpp_dt:.2f} % / K")
            print(f"  Fill Factor: {self.simulated_fill_factor():.1f} %")
        self.write_example_vseit()
        print(
            f"VSEIT example written to {self.output_folder / f'pv{self.pv_id}_example.vseit'}"
        )

    @property
    def simulation_parameters(self) -> dict:
        """All dataclass fields plus bp_folder pointing to output_folder."""
        return asdict(self) | {"bp_folder": self.output_folder}

    @property
    def dmpp_dt(self) -> float:
        """Power temperature coefficient [% / K], computed at NOCT vs. STC."""
        mpp_25 = self.simulated_mpp(irradiance=1000, temperature=25)
        mpp_noct = self.simulated_mpp(irradiance=1000, temperature=self.noct)
        return (mpp_noct - mpp_25) / (mpp_25 * (self.noct - 25)) * 100

    @property
    def cells_number(self) -> int:
        return self.rows * self.columns

    @property
    def area(self) -> float:
        """Module area [m²]."""
        return self.width * self.height

    @property
    def cell_area(self) -> float:
        return self.area / self.cells_number

    @property
    def serie(self) -> int:
        """Number of cells in series per string."""
        return self.cells_number // self.parallel

    @property
    def alpha_i(self) -> float:
        """Short-circuit current temperature coefficient [A / K]."""
        return self.alpha_i_percent * self.i_sc / 100

    @property
    def alpha_u(self) -> float:
        """Open-circuit voltage temperature coefficient [V / K]."""
        return self.alpha_u_percent * self.u_oc / 100

    def simulate(self, name: str, **kwargs) -> float:
        """Run a photovoltaic INSEL template by name and return a single float."""
        result = insel.template(
            _TEMPLATES_DIR / name,
            run_in_templates_folder=False,
            **(self.simulation_parameters | kwargs),
        )
        if isinstance(result, float):
            return result
        raise ValueError(f"Template '{name}' returned {result!r}, expected a float.")

    def simulated_u_oc(
        self, irradiance: float = 1000, temperature: float = 25
    ) -> float:
        return self.simulate("u_oc", irradiance=irradiance, temperature=temperature)

    def simulated_u_mpp(
        self, irradiance: float = 1000, temperature: float = 25
    ) -> float:
        return self.simulate("u_mpp", irradiance=irradiance, temperature=temperature)

    def simulated_i_mpp(
        self, irradiance: float = 1000, temperature: float = 25
    ) -> float:
        return self.simulate("i_mpp", irradiance=irradiance, temperature=temperature)

    def simulated_i_sc(
        self, irradiance: float = 1000, temperature: float = 25
    ) -> float:
        return self.simulate("i_sc", irradiance=irradiance, temperature=temperature)

    def simulated_mpp(self, irradiance: float = 1000, temperature: float = 25) -> float:
        return self.simulate("mpp", irradiance=irradiance, temperature=temperature)

    def simulated_fill_factor(self) -> float:
        return (
            self.simulated_mpp() / (self.simulated_u_oc() * self.simulated_i_sc()) * 100
        )

    def simulated_eta(self) -> float:
        """Simulated module efficiency at STC [%]."""
        return self.simulated_mpp() / (self.area * 1000) * 100

    @property
    def u_max(self) -> float:
        """Highest expected open-circuit voltage (1000 W/m², -25 °C) [V]."""
        return self.simulate("u_oc", irradiance=1000, temperature=-25)

    @property
    def i_max(self) -> float:
        """Highest expected short-circuit current (1000 W/m², 75 °C) [A]."""
        return self.simulate("i_sc", irradiance=1000, temperature=75)

    @property
    def p_max(self) -> float:
        """Highest expected power output (1000 W/m², -25 °C) [W]."""
        return self.simulate("mpp", irradiance=1000, temperature=-25)

    def plot(
        self,
        tty_width: int = 100,
        tty_height: int = 40,
        plots_folder: Path = Path("plots"),
    ) -> Path:
        """Render I(V) and P(V) curves at STC to a text file. Requires gnuplot.

        Sweeps voltage from 0 to u_max (u_oc at -25 °C, 1000 W/m²) in 0.1 V steps.
        Returns the path of the generated text file.
        """
        plots_folder = Path(plots_folder)
        plots_folder.mkdir(exist_ok=True, parents=True)
        insel.plot(
            _TEMPLATES_DIR / "iv_curve_text",
            u_max=math.ceil(self.u_max / 5) * 5,
            i_max=math.ceil(self.i_max) + 1,
            p_max=math.ceil(self.p_max / 50) * 5,
            tty_width=tty_width,
            tty_height=tty_height,
            plots_folder=plots_folder,
            **self.simulation_parameters,
        )
        return plots_folder / f"iv_curve_{self.pv_id}.txt"

    def write_example_vseit(self):
        from .template import Template

        bp_values = self._read_bp_values()
        bp_params = {f"bp{i + 2}": bp_values[i] for i in range(29)}
        t = Template(
            _TEMPLATES_DIR / "ivt_curves.vseit",
            run_in_templates_folder=False,
            gnuplot=True,
            name=self.name,
            u_max=math.ceil(self.u_max / 5) * 5,
            i_max=math.ceil(self.i_max) + 1,
            p_max=math.ceil(self.p_max / 50) * 5,
            **bp_params,
        )
        (self.output_folder / f"pv{self.pv_id}_example.vseit").write_text(t.content())

    def _read_bp_values(self) -> list:
        """Read the 29 parameter values from the PVDET1-generated .bp file."""
        bp_file = self.output_folder / f"pv{self.pv_id}.bp"
        values = []
        for line in bp_file.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("%"):
                continue
            value_part = stripped.split("%")[0].strip()
            if value_part:
                values.append(value_part)
        return values

    def _pvdet1_params(self) -> list:
        return [
            self.serie,
            self.parallel,
            self.cell_area,
            self.area,
            self.u_mpp,
            self.i_mpp,
            self.u_oc,
            self.alpha_u,
            self.i_sc,
            self.alpha_i,
            self.module_tolerance,
            -self.module_tolerance,
            self.height,
            self.mass,
            self.absorption_coefficient,
            self.emission_coefficient,
            self.specific_module_heat_capacity,
            self.noct,
            int(True),  # overwrite existing .bp file
            int(False),  # don't generate custom module info file
            self.maximum_voltage,
            self.width,
            self.height,
            f"pv{self.pv_id}",
            str(self.output_folder),
            self.manufacturer_name,
            self.name,
            self.module_technology,
            str(self.output_folder / "module_info.dat"),  # unused (param 20 = False)
        ]
