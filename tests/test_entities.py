"""Entity/relation API: enums, dftracer.declare_* / relate_entities and the
dft_fn.uses / generates / relate helpers.

Most tests drive a stand-in logger so they assert what pydftracer sends down to
the native module, independent of whether the installed dftracer wheel already
carries the entity API. The two tests marked ``native`` exercise the real core
when it does, since the ids are computed there (FNV-1a of sanitized type and
key, identical across languages and processes).
"""

from unittest.mock import MagicMock

import pytest
from dftracer.python import (
    EntityRelation,
    EntityRole,
    EntityStore,
    dft_fn,
    dftracer,
)
from dftracer.python.common import NoOpProfiler
from dftracer.python.env import DFTRACER_ENABLE

# A logger without the Entity* enum attributes: pydftracer then passes plain
# ints, which keeps the assertions below readable. Entity ids are whatever
# declare_entity returns, so the fake hands back a stable number per key.
LOGGER_API = [
    "initialize",
    "get_time",
    "get_config",
    "enter_event",
    "exit_event",
    "log_event",
    "log_metadata_event",
    "declare_entity",
    "declare_entity_type",
    "relate_entities",
    "set_app_metadata_int",
    "set_app_metadata_string",
    "mark_used",
    "finalize",
]

needs_enable = pytest.mark.skipif(
    not DFTRACER_ENABLE, reason="DFTRACER_ENABLE=0 makes every call a no-op"
)


def fake_logger(api=None):
    api = api or LOGGER_API
    logger = MagicMock(spec=api)
    ids = {}
    if "declare_entity" in api:
        logger.declare_entity.side_effect = lambda t, k, s, u: ids.setdefault(
            (t, k), len(ids) + 1
        )
    if "get_time" in api:
        logger.get_time.return_value = 0
    return logger


@pytest.fixture
def logger():
    """Swap the native module out of the dftracer singleton for the test."""
    tracer = dftracer.get_instance()
    original = tracer.logger
    tracer.logger = fake_logger()
    try:
        yield tracer.logger
    finally:
        tracer.logger = original


class TestEntityEnums:
    def test_store_values(self):
        assert int(EntityStore.MEMORY) == 0
        assert int(EntityStore.PARALLEL_FS) == 3
        assert int(EntityStore.OTHER) == 8

    def test_role_values(self):
        assert int(EntityRole.UNKNOWN) == 0
        assert int(EntityRole.INPUT) == 1
        assert int(EntityRole.OUTPUT) == 2

    def test_event_relations_are_below_16(self):
        """Event->entity relations are < 16, entity->entity relations >= 16.
        dft_fn.relate and dftracer.relate_entities split on that boundary."""
        for relation in (
            EntityRelation.USED,
            EntityRelation.GENERATED,
            EntityRelation.INVALIDATED,
            EntityRelation.UPDATED,
        ):
            assert int(relation) < 16
        for relation in (
            EntityRelation.DERIVED_FROM,
            EntityRelation.CONTAINS,
            EntityRelation.PART_OF,
            EntityRelation.DEPENDS_ON,
        ):
            assert int(relation) >= 16


@needs_enable
class TestDeclareEntity:
    def test_declare_entity_passes_type_key_store_uri(self, logger):
        tracer = dftracer.get_instance()
        eid = tracer.declare_entity(
            "archive", "a.tar", EntityStore.PARALLEL_FS, "/p/out/a.tar"
        )
        logger.declare_entity.assert_called_once_with(
            "archive", "a.tar", int(EntityStore.PARALLEL_FS), "/p/out/a.tar"
        )
        assert eid == 1

    def test_declare_entity_defaults_to_memory_and_empty_uri(self, logger):
        dftracer.get_instance().declare_entity("raw_sample", "sample-0")
        logger.declare_entity.assert_called_once_with(
            "raw_sample", "sample-0", int(EntityStore.MEMORY), ""
        )

    def test_declare_entity_coerces_non_string_keys(self, logger):
        dftracer.get_instance().declare_entity("step", 7)
        assert logger.declare_entity.call_args[0][1] == "7"

    def test_declare_entity_type_passes_role_and_description(self, logger):
        dftracer.get_instance().declare_entity_type(
            "raw_sample", EntityRole.INPUT, "An input sample"
        )
        logger.declare_entity_type.assert_called_once_with(
            "raw_sample", int(EntityRole.INPUT), "An input sample"
        )

    def test_declare_entity_type_defaults(self, logger):
        dftracer.get_instance().declare_entity_type("raw_sample")
        logger.declare_entity_type.assert_called_once_with(
            "raw_sample", int(EntityRole.UNKNOWN), ""
        )

    def test_relate_entities_passes_entity_relations(self, logger):
        dftracer.get_instance().relate_entities(EntityRelation.CONTAINS, 11, 22)
        logger.relate_entities.assert_called_once_with(
            int(EntityRelation.CONTAINS), 11, 22
        )

    def test_relate_entities_drops_event_relations_and_empty_ids(self, logger):
        """An event relation belongs on an event, and 0 means "never
        declared"; neither should reach the native module."""
        tracer = dftracer.get_instance()
        tracer.relate_entities(EntityRelation.USED, 11, 22)
        tracer.relate_entities(EntityRelation.CONTAINS, 0, 22)
        tracer.relate_entities(EntityRelation.CONTAINS, 11, 0)
        logger.relate_entities.assert_not_called()

    def test_entity_api_noop_without_native_support(self):
        """A native module predating the entity API has no declare_entity, so
        calls return 0 / do nothing instead of raising."""
        tracer = dftracer.get_instance()
        original = tracer.logger
        tracer.logger = fake_logger(api=["log_event", "get_time", "finalize"])
        try:
            assert tracer.declare_entity("raw_sample", "sample-0") == 0
            assert tracer.declare_entity_type("raw_sample", EntityRole.INPUT) is None
            assert tracer.relate_entities(EntityRelation.CONTAINS, 11, 22) is None
        finally:
            tracer.logger = original


@needs_enable
class TestDftFnRelations:
    def test_uses_and_generates_record_relations(self, logger):
        fn = dft_fn("PY_APP", name="transform")
        sample = fn.uses("raw_sample", "sample-0")
        structure = fn.generates("protein_structure", "MGYP0001")

        assert fn._relations[EntityRelation.USED] == [sample]
        assert fn._relations[EntityRelation.GENERATED] == [structure]
        assert sample != structure

    def test_uses_declares_the_entity_with_store_and_uri(self, logger):
        dft_fn("PY_APP", name="pack").generates(
            "archive", "a.tar", EntityStore.PARALLEL_FS, "/p/out/a.tar"
        )
        logger.declare_entity.assert_called_once_with(
            "archive", "a.tar", int(EntityStore.PARALLEL_FS), "/p/out/a.tar"
        )

    def test_relate_ignores_entity_relations_and_empty_ids(self, logger):
        fn = dft_fn("PY_APP", name="transform")
        fn.relate(EntityRelation.CONTAINS, 1234)
        fn.relate(EntityRelation.USED, 0)
        assert fn._relations == {}

        fn.relate(EntityRelation.USED, 1234)
        assert fn._relations[EntityRelation.USED] == [1234]

    def test_relations_accumulate_per_relation(self, logger):
        fn = dft_fn("PY_APP", name="transform")
        first = fn.uses("raw_sample", "sample-0")
        second = fn.uses("raw_sample", "sample-1")
        assert fn._relations[EntityRelation.USED] == [first, second]

    def test_same_entity_reused_keeps_one_id(self, logger):
        fn = dft_fn("PY_APP", name="transform")
        first = fn.uses("raw_sample", "sample-0")
        second = fn.uses("raw_sample", "sample-0")
        assert first == second

    def test_disabled_dft_fn_records_nothing(self, logger):
        fn = dft_fn("PY_APP", name="transform", enable=False)
        assert fn.uses("raw_sample", "sample-0") == 0
        assert fn.generates("protein_structure", "MGYP0001") == 0
        assert fn._relations == {}
        logger.declare_entity.assert_not_called()

    def test_relations_reach_log_event(self, logger):
        fn = dft_fn("PY_APP", name="transform")
        sample = fn.uses("raw_sample", "sample-0")
        fn.flush()

        logger.log_event.assert_called_once()
        relations = logger.log_event.call_args[1]["relations"]
        assert [list(v) for v in relations.values()] == [[sample]]

    def test_context_manager_flushes_both_relations(self, logger):
        with dft_fn("PY_APP", name="transform") as fn:
            sample = fn.uses("raw_sample", "sample-0")
            structure = fn.generates("protein_structure", "MGYP0001")

        logger.log_event.assert_called_once()
        relations = logger.log_event.call_args[1]["relations"]
        assert sorted(v for ids in relations.values() for v in ids) == sorted(
            [sample, structure]
        )

    def test_reset_clears_relations(self, logger):
        fn = dft_fn("PY_APP", name="transform")
        fn.uses("raw_sample", "sample-0")
        fn.reset()
        assert fn._relations == {}


@needs_enable
class TestNativeEntityIds:
    """Against the real native module, when it carries the entity API."""

    @pytest.fixture(autouse=True)
    def skip_without_native_entities(self):
        tracer = dftracer.get_instance()
        if not tracer._has("declare_entity"):
            pytest.skip("installed dftracer predates the entity API")
        if tracer.declare_entity("probe", "probe") == 0:
            # The core hands back DFT_ENTITY_NONE when it is not active, e.g.
            # once another test in this process has finalized it.
            pytest.skip("native tracing is not active in this process")

    def test_ids_are_stable_per_type_and_key(self):
        tracer = dftracer.get_instance()
        first = tracer.declare_entity("raw_sample", "sample-0")
        assert first != 0
        assert first == tracer.declare_entity("raw_sample", "sample-0")
        assert first != tracer.declare_entity("raw_sample", "sample-1")
        assert first != tracer.declare_entity("other_type", "sample-0")

    def test_structure_id_matches_the_c_and_cpp_tests(self):
        """FNV-1a-64("protein_structure" 0x1f "MGYP0001"), the id pinned in
        dftracer's test_entity.c / .cpp so traces agree across languages."""
        eid = dftracer.get_instance().declare_entity("protein_structure", "MGYP0001")
        assert f"{eid & 0xFFFFFFFFFFFFFFFF:016x}" == "8f0de68c04eea0bf"


class TestNoOpProfilerEntities:
    def test_entity_methods_are_noops(self):
        noop = NoOpProfiler()
        assert (
            noop.declare_entity("raw_sample", "sample-0", EntityStore.MEMORY, "") == 0
        )
        assert noop.declare_entity_type("raw_sample", EntityRole.INPUT, "d") is None
        assert noop.relate_entities(EntityRelation.CONTAINS, 1, 2) is None
        assert noop.log_metadata_event("key", "value") is None


@needs_enable
class TestMetadataEvent:
    def test_log_metadata_event_reaches_the_logger(self, logger):
        """Regression: log_metadata_event was dropped from dftracer when the
        entity API landed, breaking dft_fn.log_metadata and every caller."""
        dftracer.get_instance().log_metadata_event("epoch", "1")
        dft_fn("PY_APP", name="transform").log_metadata("step", "2")

        assert logger.log_metadata_event.call_count == 2
        assert logger.log_metadata_event.call_args_list[0][1] == {
            "key": "epoch",
            "value": "1",
        }
