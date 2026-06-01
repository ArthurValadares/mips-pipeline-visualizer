import pytest
from pipeline.ast_nodes import RType
from pipeline.graph import SimulatorGraph, PipelineConfig, BasicBlock


@pytest.fixture
def dummy_config(tmp_path):
    # Cria um config temporário para testar a leitura do YAML
    yaml_file = tmp_path / "pipeline.yml"
    yaml_file.write_text("latencies:\n  add: 2\n  default: 1")
    return PipelineConfig(str(yaml_file))


def test_pipeline_config(dummy_config):
    assert dummy_config.get_latency("add") == 2
    assert dummy_config.get_latency("sub") == 1  # Default


def test_graph_basic_blocks(dummy_config):
    inst1 = RType(op="add", label="loop")
    inst2 = RType(op="beq")  # Branch
    inst3 = RType(op="sub", index=2)

    graph = SimulatorGraph([inst1, inst2, inst3], dummy_config)

    # entry -> loop -> after_X
    assert len(graph.blocks) == 3
    assert graph.blocks[0].name == "entry"
    assert graph.blocks[1].name == "loop"
    assert graph.blocks[2].name.startswith("after_")


def test_scheduling_no_hazards(dummy_config):
    # Sem dependências RAW
    inst1 = RType(op="add", rd="r1", rs="r2", rt="r3")
    inst2 = RType(op="sub", rd="r4", rs="r5", rt="r6")

    graph = SimulatorGraph([inst1, inst2], dummy_config)
    graph.schedule()

    assert inst1.c_if == 0 and inst1.c_id == 1 and inst1.c_ex == 2
    assert inst2.c_if == 1 and inst2.c_id == 2 and inst2.c_ex == 3
    assert inst2.bubbles == 0


def test_scheduling_with_forwarding(dummy_config):
    # Dependência RAW (r1)
    inst1 = RType(op="add", rd="r1", rs="r2", rt="r3")  # Latency 2
    inst2 = RType(op="sub", rd="r4", rs="r1", rt="r6")

    graph = SimulatorGraph([inst1, inst2], dummy_config, forwarding=True)
    graph.schedule()

    # inst1 EX inicia no ciclo 2. Latência = 2. Dado pronto no ciclo 4.
    # inst2 ID ocorre no ciclo 2. Sem stalls, seu EX seria no ciclo 3.
    # Precisamos de 1 bolha para o EX da inst2 iniciar no ciclo 4.
    assert inst2.bubbles == 1
    assert inst2.c_ex == 4


def test_scheduling_without_forwarding(dummy_config):
    inst1 = RType(op="add", rd="r1", rs="r2", rt="r3")
    inst2 = RType(op="sub", rd="r4", rs="r1", rt="r6")

    graph = SimulatorGraph([inst1, inst2], dummy_config, forwarding=False)
    graph.schedule()

    # Sem forwarding, WB da inst1 ocorre em c_ex + 2 = 2 + 2 = 4.
    # inst2 precisa que o ID ocorra no ciclo 4 ou depois.
    # inst2 c_if = 1. Sem stalls, c_id seria 2. Precisamos atrasar c_id?
    # O calculo de stall atual adiciona as bolhas ANTES do EX, atrasando o EX.
    # stall = required_id_cycle (4) - inst.c_id (2) = 2 bubbles.
    assert inst2.bubbles == 2