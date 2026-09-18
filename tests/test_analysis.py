from agentredteamer.analysis import (
    _attack_success,
    direct_vs_tool,
    single_vs_multi_turn,
    success_rate_by,
    success_rate_matrix,
)


def make_trace(persona="P", defense="d1", category="c1", leaked=False, broke=False):
    return {
        "persona_name": persona,
        "defense_name": defense,
        "attack_category": category,
        "verdict": {"leaked_secret": leaked, "broke_character": broke},
    }


def test_attack_success_true_when_either_flag_set():
    assert _attack_success(make_trace(leaked=True)) is True
    assert _attack_success(make_trace(broke=True)) is True
    assert _attack_success(make_trace(leaked=True, broke=True)) is True


def test_attack_success_false_when_neither_flag_set():
    assert _attack_success(make_trace()) is False


def test_success_rate_by_computes_per_group_rate():
    traces = [
        make_trace(defense="a", leaked=True),
        make_trace(defense="a", leaked=False),
        make_trace(defense="b", leaked=False),
        make_trace(defense="b", leaked=False),
    ]
    rates = success_rate_by(traces, "defense_name")
    assert rates == {"a": 0.5, "b": 0.0}


def test_single_vs_multi_turn_splits_by_category():
    traces = [
        make_trace(category="role_play_override", leaked=True),
        make_trace(category="role_play_override", leaked=False),
        make_trace(category="multi_turn_social_engineering", leaked=True),
    ]
    result = single_vs_multi_turn(traces)
    assert result["single_turn"] == 0.5
    assert result["multi_turn"] == 1.0


def test_single_vs_multi_turn_empty_groups_default_to_zero():
    result = single_vs_multi_turn([])
    assert result == {"single_turn": 0.0, "multi_turn": 0.0}


def test_direct_vs_tool_splits_indirect_injection_separately():
    traces = [
        make_trace(category="role_play_override", leaked=False),
        make_trace(category="indirect_tool_injection", leaked=True),
        make_trace(category="indirect_tool_injection", leaked=True),
    ]
    result = direct_vs_tool(traces)
    assert result["direct"] == 0.0
    assert result["tool"] == 1.0


def test_success_rate_matrix_reports_rate_for_seen_combinations():
    traces = [make_trace(defense="a", category="x", leaked=True)]
    matrix = success_rate_matrix(traces)
    assert matrix["a"]["x"] == 1.0


def test_success_rate_matrix_missing_combination_is_none():
    # defense "a" and category "y" both appear in the data, but never together —
    # the dashboard heatmap renders that cell as "—" rather than a false 0%.
    traces = [
        make_trace(defense="a", category="x", leaked=False),
        make_trace(defense="b", category="y", leaked=False),
    ]
    matrix = success_rate_matrix(traces)
    assert matrix["a"]["y"] is None
