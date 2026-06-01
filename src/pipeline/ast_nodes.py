from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from jinja2 import Template


def svg_drawable(template_string: str):
    def decorator(cls):
        cls._svg_template = Template(template_string)

        def render_svg(self, context: Dict[str, Any]) -> str:
            return self._svg_template.render(inst=self, **context)

        cls.render_svg = render_svg
        return cls

    return decorator


@dataclass(eq=False, frozen=False)
class InstructionNode:
    op: str
    index: int = -1
    label: Optional[str] = None

    # Timings
    c_if: int = 0
    c_id: int = 0
    c_ex: int = 0
    c_mem: int = 0
    c_wb: int = 0
    bubbles: int = 0

    def get_sources(self) -> List[str]:
        return []

    def get_dests(self) -> List[str]:
        return []

    @property
    def is_branch(self) -> bool:
        return self.op.lower() in {
            "beq",
            "bne",
            "bgez",
            "j",
            "jal",
            "jr",
            "bc1t",
            "bc1f",
        }

    @property
    def text_representation(self) -> str:
        """Fallback para a representação textual"""
        return self.op


# Template Declarativo de Linha de Execução de Pipeline (Estilo Gráfico de Gantt)
ROW_TEMPLATE = """
<g transform="translate({{ x_offset }}, {{ y_offset }})">
    <rect x="0" y="0" width="{{ left_col_w }}" height="{{ row_h }}" class="{% if is_even %}inst-bg-even{% else %}inst-bg-odd{% endif %}" />
    <text class="inst-text" x="10" y="{{ row_h / 2 }}">{{ inst.text_representation }}</text>

    <g transform="translate({{ left_col_w }}, 0)">

        {% for c in range(max_cycle) %}
            <rect x="{{ c * cell_w }}" y="0" width="{{ cell_w }}" height="{{ row_h }}" class="grid-cell" />
        {% endfor %}

        <rect x="{{ inst.c_if * cell_w }}" y="0" width="{{ cell_w }}" height="{{ row_h }}" class="stage-IF" />
        <text class="stage-text" x="{{ inst.c_if * cell_w + cell_w/2 }}" y="{{ row_h/2 }}">IF</text>

        <rect x="{{ inst.c_id * cell_w }}" y="0" width="{{ cell_w }}" height="{{ row_h }}" class="stage-ID" />
        <text class="stage-text" x="{{ inst.c_id * cell_w + cell_w/2 }}" y="{{ row_h/2 }}">ID</text>

        {% if inst.bubbles > 0 %}
            {% for b in range(inst.bubbles) %}
                {% set bx = (inst.c_id + 1 + b) * cell_w %}
                <rect x="{{ bx }}" y="0" width="{{ cell_w }}" height="{{ row_h }}" fill="#FFEBEE" stroke="#fff" stroke-width="1px" />
                <circle cx="{{ bx + cell_w/2 }}" cy="{{ row_h/2 }}" r="6" fill="#E53935" />
            {% endfor %}
        {% endif %}

        <rect x="{{ inst.c_ex * cell_w }}" y="0" width="{{ cell_w }}" height="{{ row_h }}" class="stage-EX" />
        <text class="stage-text" x="{{ inst.c_ex * cell_w + cell_w/2 }}" y="{{ row_h/2 }}">EX</text>

        <rect x="{{ (inst.c_ex + 1) * cell_w }}" y="0" width="{{ cell_w }}" height="{{ row_h }}" class="stage-MEM" />
        <text class="stage-text" x="{{ (inst.c_ex + 1) * cell_w + cell_w/2 }}" y="{{ row_h/2 }}">MEM</text>

        <rect x="{{ (inst.c_ex + 2) * cell_w }}" y="0" width="{{ cell_w }}" height="{{ row_h }}" class="stage-WB" />
        <text class="stage-text" x="{{ (inst.c_ex + 2) * cell_w + cell_w/2 }}" y="{{ row_h/2 }}">WB</text>

    </g>
</g>
"""


@svg_drawable(ROW_TEMPLATE)
@dataclass(eq=False)
class RType(InstructionNode):
    rd: str = ""
    rs: str = ""
    rt: str = ""

    def get_sources(self) -> List[str]:
        # Branches como "beq r3, r2, end" caem no RType devido à sintaxe (NAME NAME, NAME, NAME).
        # Em um branch, rd e rs (r3 e r2) são fontes de leitura.
        if self.is_branch:
            return [self.rd, self.rs]
        return [self.rs, self.rt]

    def get_dests(self) -> List[str]:
        # Branches não escrevem em registradores.
        if self.is_branch:
            return []
        return [self.rd]

    @property
    def text_representation(self) -> str:
        return f"{self.op} {self.rd}, {self.rs}, {self.rt}"


@svg_drawable(ROW_TEMPLATE)
@dataclass(eq=False)
class IType(InstructionNode):
    rt: str = ""
    rs: str = ""
    imm: str = ""

    def get_sources(self) -> List[str]:
        if self.is_branch:
            return [self.rt, self.rs]
        return [self.rs]

    def get_dests(self) -> List[str]:
        if self.is_branch:
            return []
        return [self.rt]

    @property
    def text_representation(self) -> str:
        return f"{self.op} {self.rt}, {self.rs}, {self.imm}"


@svg_drawable(ROW_TEMPLATE)
@dataclass(eq=False)
class MemType(InstructionNode):
    rt: str = ""
    imm: str = ""
    rs: str = ""

    def get_sources(self) -> List[str]:
        return [self.rs] if self.op.startswith("l") else [self.rs, self.rt]

    def get_dests(self) -> List[str]:
        return [self.rt] if self.op.startswith("l") else []

    @property
    def text_representation(self) -> str:
        return f"{self.op} {self.rt}, {self.imm}({self.rs})"


@svg_drawable(ROW_TEMPLATE)
@dataclass(eq=False)
class JType(InstructionNode):
    target: str = ""

    def get_sources(self) -> List[str]:
        return []

    def get_dests(self) -> List[str]:
        return []

    @property
    def text_representation(self) -> str:
        return f"{self.op} {self.target}"


@svg_drawable(ROW_TEMPLATE)
@dataclass(eq=False)
class HaltType(InstructionNode):
    def get_sources(self) -> List[str]:
        return []

    def get_dests(self) -> List[str]:
        return []

    @property
    def text_representation(self) -> str:
        return self.op
