from interface.operations import (
    BACKEND_LIBRARIES,
    BACKEND_OPS,
    BACKEND_SPEC_OVERRIDES,
    CANONICAL_OP_SPECS,
    DEFAULTS,
    SUITE_OPS,
    VTK_OPS,
)
from interface.operations.catalog import VTK_FALLBACK_SPEC


VALID_SPEC_KEYS = {"input", "output", "option_keys", "has_options", "description", "output_required"}
VALID_INPUTS = {"file", "directory", "none", "optional"}
VALID_OUTPUTS = {"file", "directory", "display"}


def assert_valid_spec_fields(spec: dict, op: str) -> None:
    assert isinstance(spec, dict), f"{op} spec must be a dict, got {type(spec)!r}"
    assert set(spec) <= VALID_SPEC_KEYS, f"{op} has unknown spec keys: {sorted(set(spec) - VALID_SPEC_KEYS)}"
    if "input" in spec:
        assert spec["input"] in VALID_INPUTS, f"{op} has invalid input kind"
    if "output" in spec:
        assert spec["output"] in VALID_OUTPUTS, f"{op} has invalid output kind"
    if "option_keys" in spec:
        assert isinstance(spec["option_keys"], list), f"{op} option_keys must be a list"
        assert all(isinstance(key, str) for key in spec["option_keys"]), f"{op} option_keys must be strings"
    if "has_options" in spec:
        assert isinstance(spec["has_options"], bool), f"{op} has_options must be bool"
        option_keys = spec.get("option_keys")
        if spec["has_options"]:
            assert isinstance(option_keys, list), f"{op} with has_options=True must define option_keys"
            assert option_keys, f"{op} with has_options=True must define non-empty option_keys"
            assert all(isinstance(key, str) for key in option_keys), f"{op} option_keys must be strings"
        else:
            assert option_keys in (None, []), f"{op} with has_options=False cannot define option keys"
    if "description" in spec:
        assert isinstance(spec["description"], str), f"{op} description must be a string"
    if "output_required" in spec:
        assert isinstance(spec["output_required"], bool), f"{op} output_required must be bool"


def test_backend_spec_overrides_reference_canonical_specs():
    for backend, overrides in BACKEND_SPEC_OVERRIDES.items():
        assert isinstance(overrides, dict), f"{backend} overrides must be a mapping"
        for op, override in overrides.items():
            assert isinstance(override, dict), f"{backend}.{op} override must be a dict, got {type(override)!r}"
            assert op in CANONICAL_OP_SPECS, f"{backend}.{op} override has no canonical spec"
            assert_valid_spec_fields(override, f"{backend}.{op}")


def test_canonical_operation_specs_have_valid_fields():
    for op, spec in CANONICAL_OP_SPECS.items():
        assert_valid_spec_fields(spec, op)


def test_catalog_registries_reference_canonical_specs():
    referenced_ops = set()
    for ops in BACKEND_OPS.values():
        referenced_ops.update(ops)
    referenced_ops.update(VTK_OPS)
    for ops in SUITE_OPS.values():
        referenced_ops.update(ops)
    for libs in BACKEND_LIBRARIES.values():
        for ops in libs.values():
            referenced_ops.update(ops)
    for defaults in DEFAULTS.values():
        referenced_ops.update(defaults)

    missing = sorted(op for op in referenced_ops if op not in CANONICAL_OP_SPECS)
    assert not missing, f"Missing canonical op specs: {missing}"


def test_vtk_fallback_specs_are_independent_objects():
    cpp_overrides = BACKEND_SPEC_OVERRIDES["cpp"]
    canonical_ids = {id(CANONICAL_OP_SPECS[op]) for op in VTK_OPS}
    override_ids = {id(cpp_overrides[op]) for op in VTK_OPS}
    assert len(canonical_ids) == len(VTK_OPS)
    assert len(override_ids) == len(VTK_OPS)
    for op in VTK_OPS:
        assert CANONICAL_OP_SPECS[op] is not VTK_FALLBACK_SPEC
        assert cpp_overrides[op] is not VTK_FALLBACK_SPEC
        assert CANONICAL_OP_SPECS[op] is not cpp_overrides[op]
