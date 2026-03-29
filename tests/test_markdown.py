from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aas_readable import export_input, load_document_from_payload, render_document


class ViewRenderingTests(unittest.TestCase):
    def test_lossless_json_preserves_exact_engineering_fields(self) -> None:
        document = load_document_from_payload(_wrapped_sample(), source_name="wrapped.json")
        payload = render_document(document=document, format="json", view="lossless")

        self.assertEqual(payload["schema_version"], "2.0.0")
        self.assertEqual(payload["submodels"][0]["elements"][0]["typed_value"], "RoboDeburr CFRP Edge Finishing Suite")
        self.assertEqual(payload["submodels"][0]["elements"][1]["typed_value"], "APP-DEBURR-2024-0173")
        self.assertEqual(payload["element_index"]["OperationalData/CycleTime"]["nominal_value"], 18.7)
        self.assertEqual(payload["element_index"]["StaticData/SupportedSensors"]["typed_value"][0], "Keyence LJ-V series laser profile sensor")

    def test_agent_view_keeps_sensors_and_end_effectors_separate(self) -> None:
        document = load_document_from_payload(_wrapped_sample(), source_name="wrapped.json")
        payload = render_document(document=document, format="json", view="agent")
        compatibility = payload["document"]["compatibility"]

        sensor_values = [item["value"] for item in compatibility["sensors"]]
        end_effector_values = [item["value"] for item in compatibility["end_effectors"]]
        self.assertIn("Keyence LJ-V series laser profile sensor", sensor_values)
        self.assertIn("Pneumatic chamfering tool 10mm", end_effector_values)
        self.assertNotIn("Pneumatic chamfering tool 10mm", sensor_values)

    def test_agent_view_does_not_turn_robot_names_into_numeric_facts(self) -> None:
        document = load_document_from_payload(_wrapped_sample(), source_name="wrapped.json")
        payload = render_document(document=document, format="json", view="agent")
        labels = [item["label"] for item in payload["document"]["numeric_facts"]]

        self.assertIn("CycleTime", labels)
        self.assertNotIn("SupportedRobots", labels)

    def test_brief_markdown_preserves_exact_ids_and_omits_semantic_urn_noise(self) -> None:
        document = load_document_from_payload(_wrapped_sample(), source_name="wrapped.json")
        markdown = render_document(document=document, format="markdown", view="brief")

        self.assertIn("AppID: APP-DEBURR-2024-0173", markdown)
        self.assertIn("CycleTime: 18.7 s", markdown)
        self.assertNotIn("urn:test:cd:app-name", markdown)

    def test_review_markdown_includes_traceable_paths(self) -> None:
        document = load_document_from_payload(_wrapped_sample(), source_name="wrapped.json")
        markdown = render_document(document=document, format="markdown", view="review")

        self.assertIn("Path: `OperationalData/CycleTime`", markdown)
        self.assertIn("Path: `StaticData/SupportedSensors`", markdown)

    def test_wrapped_and_bare_json_match_on_lossless_overlapping_facts(self) -> None:
        wrapped_document = load_document_from_payload(_wrapped_sample(), source_name="wrapped.json")
        bare_document = load_document_from_payload(_wrapped_sample()["aas"], source_name="bare.json")

        wrapped_payload = render_document(document=wrapped_document, format="json", view="lossless")
        bare_payload = render_document(document=bare_document, format="json", view="lossless")

        self.assertEqual(
            wrapped_payload["element_index"]["StaticData/AppID"]["typed_value"],
            bare_payload["element_index"]["StaticData/AppID"]["typed_value"],
        )
        self.assertEqual(
            wrapped_payload["element_index"]["OperationalData/CycleTime"]["nominal_value"],
            bare_payload["element_index"]["OperationalData/CycleTime"]["nominal_value"],
        )

    def test_export_writes_document_artifact_for_review_view(self) -> None:
        sample = _wrapped_sample()["aas"]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            summary = export_input(input_path=input_path, output_dir=output_dir, view="review")

            self.assertEqual(summary.submodel_count, 4)
            self.assertTrue((output_dir / "index.md").exists())
            self.assertTrue((output_dir / "document.md").exists())
            self.assertTrue((output_dir / "staticdata.md").exists())


def _wrapped_sample() -> dict[str, object]:
    return {
        "narrative_summary": "Lossless test narrative.",
        "aas": {
            "assetAdministrationShells": [
                {
                    "id": "urn:test:aas:1",
                    "idShort": "ExampleAAS",
                    "assetInformation": {
                        "assetKind": "Instance",
                        "assetType": "Software",
                        "globalAssetId": "urn:test:asset:1",
                    },
                    "submodels": [
                        {"keys": [{"type": "Submodel", "value": "urn:test:sm:static"}]},
                        {"keys": [{"type": "Submodel", "value": "urn:test:sm:functional"}]},
                        {"keys": [{"type": "Submodel", "value": "urn:test:sm:operational"}]},
                        {"keys": [{"type": "Submodel", "value": "urn:test:sm:lifecycle"}]},
                    ],
                }
            ],
            "submodels": [
                {
                    "id": "urn:test:sm:static",
                    "idShort": "StaticData",
                    "semanticId": {"keys": [{"type": "GlobalReference", "value": "urn:test:cd:static"}]},
                    "submodelElements": [
                        {
                            "idShort": "AppName",
                            "modelType": "Property",
                            "value": "RoboDeburr CFRP Edge Finishing Suite",
                            "semanticId": {"keys": [{"type": "GlobalReference", "value": "urn:test:cd:app-name"}]},
                        },
                        {
                            "idShort": "AppID",
                            "modelType": "Property",
                            "value": "APP-DEBURR-2024-0173",
                        },
                        {
                            "idShort": "SupportedRobots",
                            "modelType": "Property",
                            "value": [
                                "KUKA KR 60-3",
                                "ABB IRB 4600-40/2.55",
                                "Yaskawa GP50",
                            ],
                        },
                        {
                            "idShort": "SupportedEndEffectors",
                            "modelType": "Property",
                            "value": [
                                "Pneumatic chamfering tool 10mm",
                                "Electric deburring spindle 0.5-6mm",
                            ],
                        },
                        {
                            "idShort": "SupportedSensors",
                            "modelType": "Property",
                            "value": [
                                "Keyence LJ-V series laser profile sensor",
                                "SICK Ranger3 3D camera",
                            ],
                        },
                    ],
                },
                {
                    "id": "urn:test:sm:functional",
                    "idShort": "FunctionalData",
                    "submodelElements": [
                        {
                            "idShort": "Capabilities",
                            "modelType": "Property",
                            "value": [
                                "adaptive deburring",
                                "edge chamfering",
                            ],
                        },
                        {
                            "idShort": "SupportedMaterials",
                            "modelType": "Property",
                            "value": [
                                "CFRP laminates",
                                "glass fiber composites",
                            ],
                        },
                    ],
                },
                {
                    "id": "urn:test:sm:operational",
                    "idShort": "OperationalData",
                    "submodelElements": [
                        {
                            "idShort": "CycleTime",
                            "modelType": "Property",
                            "value": 18.7,
                            "unit": "s",
                        },
                        {
                            "idShort": "AverageCycleTime",
                            "modelType": "Property",
                            "value": 19.3,
                            "unit": "s",
                        },
                        {
                            "idShort": "CPULoad",
                            "modelType": "Property",
                            "value": 63.4,
                            "unit": "%",
                        },
                    ],
                },
                {
                    "id": "urn:test:sm:lifecycle",
                    "idShort": "LifecycleData",
                    "submodelElements": [
                        {
                            "idShort": "MaintenanceInterval",
                            "modelType": "Property",
                            "value": 720,
                            "unit": "h",
                        }
                    ],
                },
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
