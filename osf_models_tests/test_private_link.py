import pytest

from website.project.model import ensure_schemas

from .factories import PrivateLinkFactory, NodeFactory
from osf_models.models import MetaSchema, DraftRegistration

@pytest.mark.django_db
def test_factory():
    plink = PrivateLinkFactory()
    assert plink.name
    assert plink.key
    assert plink.creator

# Copied from tests/test_models.py
@pytest.mark.django_db
class TestPrivateLink:

    def test_node_scale(self):
        link = PrivateLinkFactory()
        project = NodeFactory()
        comp = NodeFactory(parent=project)
        link.nodes.add(project)
        link.save()
        assert link.node_scale(project) == -40
        assert link.node_scale(comp) == -20

    # Regression test for https://sentry.osf.io/osf/production/group/1119/
    def test_to_json_nodes_with_deleted_parent(self):
        link = PrivateLinkFactory()
        project = NodeFactory(is_deleted=True)
        node = NodeFactory(parent=project)
        link.nodes.add(project, node)
        link.save()
        result = link.to_json()
        # result doesn't include deleted parent
        assert len(result['nodes']) == 1

    # Regression test for https://sentry.osf.io/osf/production/group/1119/
    def test_node_scale_with_deleted_parent(self):
        link = PrivateLinkFactory()
        project = NodeFactory(is_deleted=True)
        node = NodeFactory(parent=project)
        link.nodes.add(project, node)
        link.save()
        assert link.node_scale(node) == -40

    def test_create_from_node(self):
        ensure_schemas()
        proj = NodeFactory()
        user = proj.creator
        schema = MetaSchema.find()[0]
        data = {'some': 'data'}
        draft = DraftRegistration.create_from_node(
            proj,
            user=user,
            schema=schema,
            data=data,
        )
        assert user == draft.initiator
        assert schema == draft.registration_schema
        assert data == draft.registration_metadata
        assert proj == draft.branched_from
