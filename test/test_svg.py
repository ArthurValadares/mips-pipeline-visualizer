from pipeline.ast_nodes import HaltType
from pipeline.graph import BasicBlock
from pipeline.svg import SVGRenderer


def test_svg_renderer_headers():
    block = BasicBlock("loop")
    inst = HaltType(op="halt")
    # Força os ciclos simulando um schedule
    inst.c_if, inst.c_id, inst.c_ex, inst.bubbles = 0, 1, 2, 0
    block.instructions.append(inst)

    renderer = SVGRenderer([block], filename="meu_codigo.asm")
    svg_out = renderer.render()

    # Asserções de conteúdo crítico
    assert "<svg width=" in svg_out
    assert "meu_codigo.asm" in svg_out
    assert "Label: loop" in svg_out
    # O WB é c_ex + 2 = 4. O max_cycle é 4. max_cycle += 2 -> 6. Ciclos: 1 a 6.
    assert ">6</text>" in svg_out
