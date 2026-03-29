from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from aas_readable import export_input, load_document_from_payload, render_document, render_submodels


class StructuredViewTests(unittest.TestCase):
    def test_lossless_yaml_preserves_trace_fields(self) -> None:
        document = load_document_from_payload(_sample_payload(), source_name="sample.json")
        rendered = render_document(document=document, format="yaml", view="lossless")
        payload = yaml.safe_load(rendered)

        self.assertEqual(payload["submodels"][0]["source_pointer"]["file"], "sample.json")
        self.assertEqual(payload["element_index"]["OperationalData/CycleTime"]["source_pointer"]["element_path"], "OperationalData/CycleTime")

    def test_agent_json_groups_exact_sections(self) -> None:
        document = load_document_from_payload(_sample_payload(), source_name="sample.json")
        payload = render_document(document=document, format="json", view="agent")

        identifiers = payload["document"]["identifiers"]["fields"]
        self.assertEqual(identifiers["app_id"]["value"], "APP-QC-2024-0173")
        self.assertEqual(payload["document"]["numeric_facts"][0]["label"], "CycleTime")

    def test_review_yaml_keeps_trace_without_forcing_semantic_refs_into_brief(self) -> None:
        document = load_document_from_payload(_sample_payload(), source_name="sample.json")
        review = yaml.safe_load(render_document(document=document, format="yaml", view="review"))
        brief = render_document(document=document, format="markdown", view="brief")

        self.assertEqual(review["document"]["submodels"][0]["source_pointer"]["submodel_id_short"], "StaticData")
        self.assertNotIn("urn:test:semantic:operational", brief)

    def test_json_export_writes_document_json_for_agent_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(_sample_payload()), encoding="utf-8")

            export_input(input_path=input_path, output_dir=output_dir, output_format="json", view="agent")

            index_json = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
            document_json = json.loads((output_dir / "document.json").read_text(encoding="utf-8"))
            submodel_json = json.loads((output_dir / "operationaldata.json").read_text(encoding="utf-8"))

            self.assertEqual(index_json["view"], "agent")
            self.assertEqual(document_json["document"]["numeric_facts"][0]["label"], "CycleTime")
            self.assertEqual(submodel_json["sections"]["numeric_facts"][0]["label"], "CycleTime")

    def test_render_submodels_filters_requested_submodel(self) -> None:
        document = load_document_from_payload(_sample_payload(), source_name="sample.json")
        bundle = render_submodels(document=document, include=["Operational Data"], format="json", view="review")

        self.assertEqual(len(bundle["submodels"]), 1)
        self.assertEqual(bundle["submodels"][0]["id_short"], "OperationalData")


def _sample_payload() -> dict[str, object]:
    return {
        "assetAdministrationShells": [
            {
                "id": "urn:test:aas:1",
                "idShort": "ExampleAAS",
                "assetInformation": {"assetKind": "Instance", "globalAssetId": "urn:test:asset:1"},
                "submodels": [
                    {"keys": [{"type": "Submodel", "value": "urn:test:sm:static"}]},
                    {"keys": [{"type": "Submodel", "value": "urn:test:sm:operational"}]},
                ],
            }
        ],
        "submodels": [
            {
                "id": "urn:test:sm:static",
                "idShort": "StaticData",
                "submodelElements": [
                    {"idShort": "AppName", "modelType": "Property", "value": "Inline Composite QC"},
                    {"idShort": "AppID", "modelType": "Property", "value": "APP-QC-2024-0173"},
                    {"idShort": "SupportedSensors", "modelType": "Property", "value": ["Laser gauge", "3D camera"]},
                ],
            },
            {
                "id": "urn:test:sm:operational",
                "idShort": "OperationalData",
                "semanticId": {"keys": [{"type": "GlobalReference", "value": "urn:test:semantic:operational"}]},
                "submodelElements": [
                    {"idShort": "CycleTime", "modelType": "Property", "value": 3.5, "unit": "s"},
                    {"idShort": "MemoryUsage", "modelType": "Property", "value": 1843, "unit": "MB"},
                ],
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
