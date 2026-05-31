from pipeline.ast_nodes import RType, IType, MemType, JType, HaltType


def test_rtype_standard():
    inst = RType(op="add", rd="r1", rs="r2", rt="r3")
    assert not inst.is_branch
    assert inst.get_sources() == ["r2", "r3"]
    assert inst.get_dests() == ["r1"]
    assert inst.text_representation == "add r1, r2, r3"


def test_rtype_branch():
    inst = RType(op="beq", rd="r1", rs="r2", rt="label")
    assert inst.is_branch
    assert inst.get_sources() == ["r1", "r2"]
    assert inst.get_dests() == []


def test_itype_standard():
    inst = IType(op="daddi", rt="r1", rs="r2", imm="10")
    assert not inst.is_branch
    assert inst.get_sources() == ["r2"]
    assert inst.get_dests() == ["r1"]
    assert inst.text_representation == "daddi r1, r2, 10"


def test_memtype_load():
    inst = MemType(op="lw", rt="r1", imm="0", rs="r2")
    assert inst.get_sources() == ["r2"]
    assert inst.get_dests() == ["r1"]
    assert inst.text_representation == "lw r1, 0(r2)"


def test_memtype_store():
    inst = MemType(op="sw", rt="r1", imm="0", rs="r2")
    assert inst.get_sources() == ["r2", "r1"]
    assert inst.get_dests() == []


def test_jtype_and_halt():
    j_inst = JType(op="j", target="loop")
    assert j_inst.get_sources() == []
    assert j_inst.get_dests() == []
    assert j_inst.text_representation == "j loop"

    halt_inst = HaltType(op="halt")
    assert halt_inst.get_sources() == []
    assert halt_inst.get_dests() == []
    assert halt_inst.text_representation == "halt"


def test_svg_drawable_rendering():
    inst = HaltType(op="halt", index=0)
    inst.c_if, inst.c_id, inst.c_ex, inst.bubbles = 0, 1, 2, 0

    # Renderiza com um contexto fictício
    context = {"x_offset": 0, "y_offset": 0, "left_col_w": 100, "cell_w": 40, "row_h": 30, "is_even": True,
               "max_cycle": 5}
    svg_output = inst.render_svg(context)

    assert "<g transform=" in svg_output
    assert "halt" in svg_output
