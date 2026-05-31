from typing import List
from .graph import BasicBlock


class SVGRenderer:
    def __init__(self, blocks: List[BasicBlock], filename: str = "Pipeline"):
        self.blocks = blocks
        self.filename = filename

    def render(self) -> str:
        max_cycle = 0
        total_insts = 0
        for block in self.blocks:
            total_insts += len(block.instructions)
            for inst in block.instructions:
                wb_cycle = inst.c_ex + 2
                if wb_cycle > max_cycle:
                    max_cycle = wb_cycle

        max_cycle += 2

        row_h = 32
        cell_w = 40
        left_col_w = 220
        width = left_col_w + (max_cycle * cell_w)

        height = row_h + (total_insts * row_h) + (len(self.blocks) * row_h) + 20

        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background-color: #FAFAFA; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;">',
            "<defs>",
            "    <style>",
            "        .header-cell { fill: #1976D2; stroke: #fff; stroke-width: 1px; }",
            "        .header-text { fill: #fff; font-size: 13px; text-anchor: middle; dominant-baseline: central; font-weight: bold; }",
            "        .grid-cell { fill: none; stroke: #E0E0E0; stroke-width: 1px; }",
            "        .inst-bg-even { fill: #F4F9FD; stroke: #E0E0E0; stroke-width: 1px; }",
            "        .inst-bg-odd { fill: #FFFFFF; stroke: #E0E0E0; stroke-width: 1px; }",
            "        .inst-text { fill: #333; font-size: 13px; dominant-baseline: central; font-family: monospace; }",
            "        .block-title { fill: #546E7A; font-size: 14px; font-weight: bold; dominant-baseline: central; }",
            "        .stage-IF { fill: #2EBA68; stroke: #fff; stroke-width: 1px; }",
            "        .stage-ID { fill: #1DA1F2; stroke: #fff; stroke-width: 1px; }",
            "        .stage-EX { fill: #FFA000; stroke: #fff; stroke-width: 1px; }",
            "        .stage-MEM { fill: #9C27B0; stroke: #fff; stroke-width: 1px; }",
            "        .stage-WB { fill: #F44336; stroke: #fff; stroke-width: 1px; }",
            "        .stage-text { fill: #fff; font-size: 12px; font-weight: bold; text-anchor: middle; dominant-baseline: central; }",
            "    </style>",
            "</defs>",
        ]

        # Caixa superior esquerda contendo o nome do arquivo
        svg_parts.append(
            f'<rect class="header-cell" x="0" y="0" width="{left_col_w}" height="{row_h}" />'
        )
        svg_parts.append(
            f'<text class="header-text" x="10" y="{row_h / 2}" style="text-anchor: start;">File: {self.filename}</text>'
        )

        # Cabeçalho Global dos Ciclos (O visual exibe ciclo de 1 a Max)
        svg_parts.append(f'<g transform="translate({left_col_w}, 0)">')
        for c in range(max_cycle):
            x = c * cell_w
            svg_parts.append(
                f'<rect class="header-cell" x="{x}" y="0" width="{cell_w}" height="{row_h}" />'
            )
            svg_parts.append(
                f'<text class="header-text" x="{x + cell_w / 2}" y="{row_h / 2}">{c + 1}</text>'
            )
        svg_parts.append("</g>")

        y_offset = row_h
        inst_counter = 0

        for block in self.blocks:
            # Ignora o "entry" e os blocos automáticos criados após os branches ("after_...")
            if block.name != "entry" and not block.name.startswith("after_"):
                svg_parts.append(f'<g transform="translate(0, {y_offset})">')
                svg_parts.append(
                    f'<rect x="0" y="0" width="{width}" height="{row_h}" fill="#ECEFF1" stroke="#E0E0E0"/>'
                )
                svg_parts.append(
                    f'<text class="block-title" x="10" y="{row_h / 2}">Label: {block.name}</text>'
                )
                svg_parts.append("</g>")
                y_offset += row_h

            for inst in block.instructions:
                context = {
                    "x_offset": 0,
                    "y_offset": y_offset,
                    "left_col_w": left_col_w,
                    "cell_w": cell_w,
                    "row_h": row_h,
                    "is_even": inst_counter % 2 == 0,
                    "max_cycle": max_cycle,
                }

                svg_parts.append(inst.render_svg(context))

                y_offset += row_h
                inst_counter += 1

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)
