from click.testing import CliRunner

from pipeline.ast_nodes import RType, JType, HaltType
from pipeline.main import main, MIPSBuilder


def test_mips_builder_transforms():
    builder = MIPSBuilder()

    # Testa label
    builder.label(["meu_label"])
    assert builder.current_label == "meu_label"

    # Testa instrução R_Type (deve consumir o label)
    inst_r = builder.r_type(["add", "r1", "r2", "r3"])
    assert isinstance(inst_r, RType)
    assert inst_r.label == "meu_label"
    assert builder.current_label is None  # Label consumido

    # Testa JType e Halt
    inst_j = builder.j_type(["j", "loop"])
    assert isinstance(inst_j, JType)

    inst_halt = builder.halt_inst(["halt"])
    assert isinstance(inst_halt, HaltType)
    assert inst_halt.op == "halt"


def test_cli_execution(mocker, tmp_path):
    runner = CliRunner()

    input_file = tmp_path / "test.asm"
    input_file.write_text("daddi r1, r0, 0\nadd r1, r1, r1\nhalt\n")

    output_file = tmp_path / "out.svg"

    # Mock do parse para não depender do grammar.lark externo real no teste de CLI
    mock_parser = mocker.patch("pipeline.main.Lark")
    mock_tree = mocker.Mock()
    mock_tree.children = [HaltType(op="halt", index=0)]
    mock_parser.return_value.parse.return_value = mock_tree

    result = runner.invoke(main, [str(input_file), str(output_file)])

    assert result.exit_code == 0
    assert "Gerado:" in result.output
    assert output_file.exists()
