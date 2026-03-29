from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from aas_readable.exporter import export_input_to_markdown


class YamlExportTests(unittest.TestCase):
    def test_default_export_still_writes_only_markdown(self) -> None:
        sample = {
            "assetAdministrationShells": [{"id": "urn:test:aas:1", "idShort": "ExampleAAS"}],
            "submodels": [{"id": "urn:test:sm:1", "idShort": "StaticData", "submodelElements": []}],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            export_input_to_markdown(input_path=input_path, output_dir=output_dir)

            self.assertTrue((output_dir / "index.md").exists())
            self.assertTrue((output_dir / "llm-context.md").exists())
            self.assertTrue((output_dir / "staticdata.md").exists())
            self.assertFalse((output_dir / "index.yaml").exists())
            self.assertFalse((output_dir / "llm-context.yaml").exists())
            self.assertFalse((output_dir / "staticdata.yaml").exists())

    def test_yaml_export_writes_companion_artifacts(self) -> None:
        sample = {
            "assetAdministrationShells": [
                {
                    "id": "urn:test:aas:1",
                    "idShort": "ExampleAAS",
                    "assetInformation": {"assetKind": "Instance"},
                }
            ],
            "submodels": [
                {
                    "id": "urn:test:sm:1",
                    "idShort": "TechnicalData",
                    "kind": "Instance",
                    "submodelElements": [
                        {
                            "idShort": "Nameplate",
                            "modelType": "SubmodelElementCollection",
                            "value": [
                                {
                                    "idShort": "SerialNumber",
                                    "modelType": "Property",
                                    "value": "SN-42",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            export_input_to_markdown(
                input_path=input_path,
                output_dir=output_dir,
                output_format="both",
            )

            self.assertTrue((output_dir / "index.yaml").exists())
            self.assertTrue((output_dir / "llm-context.yaml").exists())
            self.assertTrue((output_dir / "technicaldata.yaml").exists())

            index_yaml = yaml.safe_load((output_dir / "index.yaml").read_text(encoding="utf-8"))
            self.assertEqual(index_yaml["source"]["file"], "sample.json")
            self.assertEqual(index_yaml["source"]["exported_submodel_count"], 1)
            self.assertEqual(index_yaml["submodels"][0]["markdown_file"], "technicaldata.md")
            self.assertEqual(index_yaml["submodels"][0]["yaml_file"], "technicaldata.yaml")
            self.assertEqual(index_yaml["llm_context_file"], "llm-context.yaml")

    def test_yaml_submodel_export_preserves_nested_children(self) -> None:
        sample = {
            "assetAdministrationShells": [],
            "submodels": [
                {
                    "id": "urn:test:sm:1",
                    "idShort": "TechnicalData",
                    "kind": "Instance",
                    "submodelElements": [
                        {
                            "idShort": "Nameplate",
                            "modelType": "SubmodelElementCollection",
                            "value": [
                                {
                                    "idShort": "SerialNumber",
                                    "modelType": "Property",
                                    "value": "SN-42",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            export_input_to_markdown(
                input_path=input_path,
                output_dir=output_dir,
                output_format="yaml",
            )

            submodel_yaml = yaml.safe_load((output_dir / "technicaldata.yaml").read_text(encoding="utf-8"))
            self.assertEqual(submodel_yaml["id"], "urn:test:sm:1")
            self.assertEqual(submodel_yaml["elements"][0]["id_short"], "Nameplate")
            self.assertNotIn("value", submodel_yaml["elements"][0])
            self.assertEqual(submodel_yaml["elements"][0]["children"][0]["id_short"], "SerialNumber")
            self.assertEqual(submodel_yaml["elements"][0]["children"][0]["value"], "SN-42")

    def test_wrapped_json_includes_canonical_text_in_llm_context_yaml(self) -> None:
        wrapped = {
            "canonical_text": "This application inspects drill quality in an aerospace line.",
            "aas": {
                "assetAdministrationShells": [{"id": "urn:test:aas:2", "idShort": "NorthWingDrillTrace"}],
                "submodels": [
                    {
                        "id": "urn:test:submodel:static",
                        "idShort": "StaticData",
                        "submodelElements": [],
                    }
                ],
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "wrapped.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(wrapped), encoding="utf-8")

            export_input_to_markdown(
                input_path=input_path,
                output_dir=output_dir,
                output_format="yaml",
            )

            llm_context_yaml = yaml.safe_load((output_dir / "llm-context.yaml").read_text(encoding="utf-8"))
            self.assertEqual(
                llm_context_yaml["canonical_text"],
                "This application inspects drill quality in an aerospace line.",
            )

    def test_include_filter_limits_yaml_outputs(self) -> None:
        sample = {
            "assetAdministrationShells": [{"id": "urn:test:aas:1", "idShort": "ExampleAAS"}],
            "submodels": [
                {"id": "urn:test:sm:1", "idShort": "StaticData", "submodelElements": []},
                {"id": "urn:test:sm:2", "idShort": "OperationalData", "submodelElements": []},
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            export_input_to_markdown(
                input_path=input_path,
                output_dir=output_dir,
                include=["Operational Data"],
                output_format="yaml",
            )

            self.assertTrue((output_dir / "operationaldata.yaml").exists())
            self.assertFalse((output_dir / "staticdata.yaml").exists())

    def test_yaml_omits_empty_optional_fields_and_keeps_top_level_order(self) -> None:
        sample = {
            "assetAdministrationShells": [{"id": "urn:test:aas:1", "idShort": "ExampleAAS"}],
            "submodels": [
                {
                    "id": "urn:test:sm:1",
                    "idShort": "StaticData",
                    "kind": "",
                    "submodelElements": [{"idShort": "Status", "modelType": "Property", "value": "ok"}],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            export_input_to_markdown(
                input_path=input_path,
                output_dir=output_dir,
                output_format="yaml",
            )

            yaml_text = (output_dir / "staticdata.yaml").read_text(encoding="utf-8")
            self.assertEqual(yaml_text.splitlines()[:3], ["id: urn:test:sm:1", "id_short: StaticData", "elements:"])
            self.assertNotIn("kind:", yaml_text)
            self.assertNotIn("semantic_id:", yaml_text)
            self.assertNotIn("description:", yaml_text)

    def test_yaml_only_export_does_not_write_markdown_files(self) -> None:
        sample = {
            "assetAdministrationShells": [{"id": "urn:test:aas:1", "idShort": "ExampleAAS"}],
            "submodels": [{"id": "urn:test:sm:1", "idShort": "StaticData", "submodelElements": []}],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            export_input_to_markdown(
                input_path=input_path,
                output_dir=output_dir,
                output_format="yaml",
            )

            self.assertTrue((output_dir / "index.yaml").exists())
            self.assertTrue((output_dir / "llm-context.yaml").exists())
            self.assertTrue((output_dir / "staticdata.yaml").exists())
            self.assertFalse((output_dir / "index.md").exists())
            self.assertFalse((output_dir / "llm-context.md").exists())
            self.assertFalse((output_dir / "staticdata.md").exists())

    def test_json_export_writes_machine_readable_bundle(self) -> None:
        sample = {
            "assetAdministrationShells": [{"id": "urn:test:aas:1", "idShort": "ExampleAAS"}],
            "submodels": [
                {
                    "id": "urn:test:sm:1",
                    "idShort": "OperationalData",
                    "submodelElements": [
                        {
                            "idShort": "CycleTime",
                            "modelType": "Property",
                            "value": "3.5",
                            "unit": "s",
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            export_input_to_markdown(
                input_path=input_path,
                output_dir=output_dir,
                output_format="json",
                profile="agent-structured",
            )

            index_json = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
            llm_context_json = json.loads((output_dir / "llm-context.json").read_text(encoding="utf-8"))
            submodel_json = json.loads((output_dir / "operationaldata.json").read_text(encoding="utf-8"))

            self.assertEqual(index_json["schema_version"], "1.0.0")
            self.assertEqual(index_json["submodels"][0]["artifacts"]["json"], ["operationaldata.json"])
            self.assertIn("prompt_text", llm_context_json)
            self.assertEqual(submodel_json["elements"][0]["path"], "OperationalData/CycleTime")
            self.assertEqual(submodel_json["elements"][0]["normalized_unit"], "s")


if __name__ == "__main__":
    unittest.main()
