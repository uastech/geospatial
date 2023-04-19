import os.path
from dataclasses import dataclass
import json
from pathlib import Path
from typing import List

import bc_jsonpath_ng
import jsonschema.validators
import yaml


@dataclass
class ValidationError(object):
    """Error encountered while validating an instance against a schema."""

    message: str
    """Validation error message."""

    json_path: str
    """Location of the data causing the validation error."""


def _collect_errors(e: jsonschema.ValidationError) -> List[ValidationError]:
    if e.context:
        result = []
        for child in e.context:
            result.extend(_collect_errors(child))
        return result
    else:
        return [ValidationError(message=e.message, json_path=e.json_path)]


def validate(openapi_path: str, object_path: str, instance: dict) -> List[ValidationError]:
    with open(openapi_path, "r") as f:
        openapi_content = yaml.full_load(f)

    schema_matches = bc_jsonpath_ng.parse(object_path).find(openapi_content)
    if len(schema_matches) != 1:
        raise ValueError(
            f"Found {len(schema_matches)} matches to JSON path '{object_path}' within OpenAPI definition when expecting exactly 1 match"
        )
    schema = schema_matches[0].value

    openapi_version = openapi_content["openapi"]
    if openapi_version.startswith("3.0"):
        # https://github.com/OAI/OpenAPI-Specification/blob/main/schemas/v3.0/schema.json#L3
        validator_class = jsonschema.Draft4Validator
    elif openapi_version.startswith("3.1"):
        # https://github.com/OAI/OpenAPI-Specification/blob/main/schemas/v3.1/schema.json#L3
        validator_class = jsonschema.Draft202012Validator
    else:
        raise NotImplementedError(
            f"Cannot determine which JSON Schema validator to use for OpenAPI version {openapi_version}"
        )

    validator_class.check_schema(schema)

    ref_resolver = jsonschema.RefResolver(f"{Path(openapi_path).as_uri()}", openapi_content)
    validator = validator_class(schema, resolver=ref_resolver)
    result = []
    for e in validator.iter_errors(instance):
        result.extend(_collect_errors(e))
    return result


def main():
    root = os.path.realpath(os.path.join(os.path.split(__file__)[0], ".."))

    openapi_path = os.path.join(root, "geospatial.yaml")

    instance_path = os.path.join(root, "examples/test.json")
    with open(instance_path, "r") as f:
        instance_content = json.load(f)

    errors = validate(openapi_path, "$.components.schemas.FeatureCollection", instance_content)
    if errors:
        for e in errors:
            print(f"{e.json_path}: {e.message}")
            print()
    else:
        print("No errors found.")


if __name__ == "__main__":
    main()
