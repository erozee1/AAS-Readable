from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aasx_md_exporter.exporter import export_input_to_markdown


class MarkdownRenderingTests(unittest.TestCase):
    def test_rendered_export_contains_submodel_and_llm_context(self) -> None:
        sample = {
            "assetAdministrationShells": [
                {
                    "id": "urn:test:aas:1",
                    "idShort": "ExampleAAS",
                    "assetInformation": {
                        "assetKind": "Instance",
                        "assetType": "TestAsset",
                        "globalAssetId": "urn:test:asset:1",
                    },
                    "submodels": [
                        {
                            "keys": [
                                {
                                    "type": "Submodel",
                                    "value": "urn:test:submodel:technical-data",
                                }
                            ]
                        }
                    ],
                }
            ],
            "submodels": [
                {
                    "id": "urn:test:submodel:technical-data",
                    "idShort": "TechnicalData",
                    "kind": "Instance",
                    "description": [{"language": "en", "text": "Technical metadata"}],
                    "submodelElements": [
                        {
                            "idShort": "RatedVoltage",
                            "modelType": "Property",
                            "value": "400",
                            "valueType": "xs:int",
                            "unit": "V",
                        },
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
                        },
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            summary = export_input_to_markdown(input_path=input_path, output_dir=output_dir)

            self.assertEqual(summary.submodel_count, 1)
            self.assertEqual(summary.asset_shell_count, 1)
            self.assertTrue((output_dir / "index.md").exists())
            self.assertTrue((output_dir / "technicaldata.md").exists())
            self.assertTrue((output_dir / "llm-context.md").exists())

            llm_context = (output_dir / "llm-context.md").read_text(encoding="utf-8")
            self.assertIn("# AAS LLM Context", llm_context)
            self.assertIn("### ExampleAAS", llm_context)
            self.assertIn("`RatedVoltage`", llm_context)

    def test_wrapped_meng_style_json_uses_canonical_text(self) -> None:
        wrapped = {
            "canonical_text": "This application inspects drill quality in an aerospace line.",
            "aas": {
                "assetAdministrationShells": [
                    {
                        "id": "urn:test:aas:2",
                        "idShort": "NorthWingDrillTrace",
                    }
                ],
                "submodels": [
                    {
                        "id": "urn:test:submodel:static",
                        "idShort": "StaticData",
                        "submodelElements": [
                            {
                                "idShort": "AppName",
                                "modelType": "Property",
                                "value": "NorthWing Airframe Drill Trace",
                            }
                        ],
                    }
                ],
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "wrapped.json"
            output_dir = tmp_path / "out"
            input_path.write_text(json.dumps(wrapped), encoding="utf-8")

            export_input_to_markdown(input_path=input_path, output_dir=output_dir)

            llm_context = (output_dir / "llm-context.md").read_text(encoding="utf-8")
            self.assertIn("This application inspects drill quality in an aerospace line.", llm_context)

    def test_render_submodel_markdown_renders_nested_children(self) -> None:
        sample = {
            "assetAdministrationShells": [],
            "submodels": [
                {
                    "id": "urn:test:submodel",
                    "idShort": "Technical Data",
                    "kind": "INSTANCE",
                    "submodelElements": [
                        {
                            "idShort": "Rated Voltage",
                            "modelType": "Property",
                            "value": "400",
                            "unit": "V",
                        },
                        {
                            "idShort": "Nameplate",
                            "modelType": "SubmodelElementCollection",
                            "value": [
                                {
                                    "idShort": "Serial Number",
                                    "modelType": "Property",
                                    "value": "SN-42",
                                }
                            ],
                        },
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            input_path.write_text(json.dumps(sample), encoding="utf-8")
            result = export_input_to_markdown(input_path=input_path, output_dir=tmp_path / "out")
            markdown = (tmp_path / "out" / "technical-data.md").read_text(encoding="utf-8")

            self.assertEqual(result.submodel_count, 1)
            self.assertIn("# Technical Data", markdown)
            self.assertIn("### Rated Voltage", markdown)
            self.assertIn("- Unit: `V`", markdown)
            self.assertIn("#### Serial Number", markdown)

    def test_include_filter_only_writes_requested_submodel(self) -> None:
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

            summary = export_input_to_markdown(
                input_path=input_path,
                output_dir=output_dir,
                include=["Operational Data"],
            )

            self.assertEqual(summary.submodel_count, 1)
            self.assertTrue((output_dir / "operationaldata.md").exists())
            self.assertFalse((output_dir / "staticdata.md").exists())

    def test_non_empty_output_dir_requires_overwrite(self) -> None:
        sample = {
            "assetAdministrationShells": [{"id": "urn:test:aas:1", "idShort": "ExampleAAS"}],
            "submodels": [{"id": "urn:test:sm:1", "idShort": "StaticData", "submodelElements": []}],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.json"
            output_dir = tmp_path / "out"
            output_dir.mkdir()
            (output_dir / "existing.txt").write_text("keep", encoding="utf-8")
            input_path.write_text(json.dumps(sample), encoding="utf-8")

            with self.assertRaises(FileExistsError):
                export_input_to_markdown(input_path=input_path, output_dir=output_dir)


if __name__ == "__main__":
    unittest.main()
