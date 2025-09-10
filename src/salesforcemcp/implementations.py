import salesforcemcp.sfdc_client as sfdc_client
from salesforcemcp.sfdc_client import OrgHandler
import mcp.types as types
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceError
import json
from typing import Any

def create_object_impl(sf_client: sfdc_client.OrgHandler, arguments: dict[str, str]):
    """Creates a new custom object via the Salesforce Tooling API using the simple-salesforce client."""
    name = arguments.get("name")
    plural_name = arguments.get("plural_name")
    api_name = arguments.get("api_name")

    if not sf_client.connection:
        return [types.TextContent(
            type="text", 
            text="Salesforce connection is not active. Cannot perform metadata deployment."
        )]

    mdapi = sf_client.connection.mdapi

    custom_object = mdapi.CustomObject(
        fullName=api_name,
        label=name,
        pluralLabel=plural_name,
        nameField=mdapi.CustomField(
            label="Name",
            type=mdapi.FieldType("Text")
        ),
        deploymentStatus=mdapi.DeploymentStatus("Deployed"),
        sharingModel=mdapi.SharingModel("Read")
    )
    
    try:
        mdapi.CustomObject.create(custom_object)
        return [types.TextContent(
            type="text", 
            text=f"Custom Object '{api_name}' created successfully"
        )]
    except SalesforceError as e:
        return [types.TextContent(
            type="text", 
            text=f"Error creating custom object: {e}"
        )]

def create_object_with_fields_impl(sf_client: sfdc_client.OrgHandler, arguments: dict[str, str]):
    """Creates a new custom object with fields via the Metadata API."""
    name = arguments.get("name")
    plural_name = arguments.get("plural_name")
    api_name = arguments.get("api_name")
    description = arguments.get("description")
    fields = arguments.get("fields")

    json_obj = {}
    json_obj["name"] = name
    json_obj["plural_name"] = plural_name
    json_obj["api_name"] = api_name
    json_obj["description"] = description
    json_obj["fields"] = fields

    if not sf_client.connection:
        return [types.TextContent(
            type="text", 
            text="Salesforce connection is not active. Cannot perform metadata deployment."
        )]
    
    sfdc_client.write_to_file(json.dumps(json_obj))
    sfdc_client.create_metadata_package(json_obj)
    sfdc_client.create_send_to_server(sf_client.connection)

    return [
        types.TextContent(
            type="text",
            text=f"Custom Object '{api_name}' creation package prepared and deployment initiated."
        )
    ]

# --- Data Query Implementations ---

def run_soql_query_impl(sf_client: OrgHandler, arguments: dict[str, str]):
    """Executes a SOQL query against Salesforce."""
    query = arguments.get("query")
    if not query:
        return [types.TextContent(type="text", text="Missing 'query' argument")]
    if not sf_client.connection:
        return [types.TextContent(type="text", text="Salesforce connection not established.")]
    
    try:
        results = sf_client.connection.query_all(query)
        return [
            types.TextContent(
                type="text",
                text=f"SOQL Query Results (JSON):\n{json.dumps(results, indent=2)}"
            )
        ]
    except SalesforceError as e:
        return [types.TextContent(type="text", text=f"SOQL Error: {e.status} {e.resource_name} {e.content}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error executing SOQL: {e}")]

def run_sosl_search_impl(sf_client: OrgHandler, arguments: dict[str, str]):
    """Executes a SOSL search against Salesforce."""
    search = arguments.get("search")
    if not search:
        return [types.TextContent(type="text", text="Missing 'search' argument")]
    if not sf_client.connection:
        return [types.TextContent(type="text", text="Salesforce connection not established.")]
    
    try:
        results = sf_client.connection.search(search)
        return [
            types.TextContent(
                type="text",
                text=f"SOSL Search Results (JSON):\n{json.dumps(results, indent=2)}"
            )
        ]
    except SalesforceError as e:
        return [types.TextContent(type="text", text=f"SOSL Error: {e.status} {e.resource_name} {e.content}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error executing SOSL: {e}")]

def get_object_fields_impl(sf_client: OrgHandler, arguments: dict[str, str]):
    """Retrieves detailed information about the fields of a Salesforce object."""
    object_name = arguments.get("object_name")
    if not object_name:
        return [types.TextContent(type="text", text="Missing 'object_name' argument")]
    
    try:
        results = sf_client.get_object_fields_cached(object_name)
        return [
            types.TextContent(
                type="text",
                text=f"{object_name} Fields Metadata (JSON):\n{json.dumps(results, indent=2)}"
            )
        ]
    except Exception as e:
         return [types.TextContent(type="text", text=f"Error getting fields for {object_name}: {e}")]

def describe_object_impl(sf_client: OrgHandler, arguments: dict[str, Any]):
    """Get detailed schema information for a Salesforce object, formatted as markdown."""
    object_name = arguments.get("object_name")
    include_field_details = arguments.get("include_field_details", True)
    if not object_name:
        return [types.TextContent(type="text", text="Missing 'object_name' argument")]  
    if not sf_client.connection:
        return [types.TextContent(type="text", text="Salesforce connection not established.")]
    
    try:
        sf_object = getattr(sf_client.connection, object_name)
        describe = sf_object.describe()
        
        # Basic object info
        result = f"## {describe['label']} ({describe['name']})\n\n"
        result += f"**Type:** {'Custom Object' if describe.get('custom') else 'Standard Object'}\n"
        result += f"**API Name:** {describe['name']}\n"
        result += f"**Label:** {describe['label']}\n"
        result += f"**Plural Label:** {describe.get('labelPlural', '')}\n"
        result += f"**Key Prefix:** {describe.get('keyPrefix', 'N/A')}\n"
        result += f"**Createable:** {describe.get('createable')}\n"
        result += f"**Updateable:** {describe.get('updateable')}\n"
        result += f"**Deletable:** {describe.get('deletable')}\n\n"
        
        if include_field_details:
            # Fields table
            result += "## Fields\n\n"
            result += "| API Name | Label | Type | Required | Unique | External ID |\n"
            result += "|----------|-------|------|----------|--------|------------|\n"
            for field in describe["fields"]:
                required = "Yes" if not field.get("nillable", True) else "No"
                unique = "Yes" if field.get("unique", False) else "No"
                external_id = "Yes" if field.get("externalId", False) else "No"
                result += f"| {field['name']} | {field['label']} | {field['type']} | {required} | {unique} | {external_id} |\n"
            
            # Relationship fields
            reference_fields = [
                f for f in describe["fields"] if f["type"] == "reference" and f.get("referenceTo")
            ]
            if reference_fields:
                result += "\n## Relationship Fields\n\n"
                result += "| API Name | Related To | Relationship Name |\n"
                result += "|----------|-----------|-------------------|\n"
                for field in reference_fields:
                    related_to = ", ".join(field["referenceTo"])
                    rel_name = field.get("relationshipName", "N/A")
                    result += f"| {field['name']} | {related_to} | {rel_name} |\n"
            
            # Picklist fields
            picklist_fields = [
                f for f in describe["fields"]
                if f["type"] in ("picklist", "multipicklist") and f.get("picklistValues")
            ]
            if picklist_fields:
                result += "\n## Picklist Fields\n\n"
                for field in picklist_fields:
                    result += f"### {field['label']} ({field['name']})\n\n"
                    result += "| Value | Label | Default |\n"
                    result += "|-------|-------|--------|\n"
                    for value in field["picklistValues"]:
                        is_default = "Yes" if value.get("defaultValue", False) else "No"
                        result += f"| {value['value']} | {value['label']} | {is_default} |\n"
                    result += "\n"
        
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error describing object {object_name}: {str(e)}")]

# --- Einstein Studio Model Implementations ---

def create_einstein_model_impl(sf_client: OrgHandler, arguments: dict[str, Any]):
    """Creates an Einstein Studio model using AppFrameworkTemplateBundle."""
    model_name = arguments.get("model_name")
    description = arguments.get("description")
    model_capability = arguments.get("model_capability", "BinaryClassification")
    outcome_field = arguments.get("outcome_field")
    goal = arguments.get("goal", "Maximize")
    data_source = arguments.get("data_source")
    success_value = arguments.get("success_value", "true")
    failure_value = arguments.get("failure_value", "false")
    algorithm_type = arguments.get("algorithm_type", "XGBoost")
    fields = arguments.get("fields", [])

    # Validate required fields
    if not all([model_name, description, outcome_field, data_source, fields]):
        return [types.TextContent(
            type="text", 
            text="Missing required fields: model_name, description, outcome_field, data_source, and fields are required"
        )]

    if not sf_client.connection:
        return [types.TextContent(
            type="text", 
            text="Salesforce connection is not active. Cannot perform metadata deployment."
        )]

    try:
        # Create Einstein Studio model package
        json_obj = {
            "model_name": model_name,
            "description": description,
            "model_capability": model_capability,
            "outcome_field": outcome_field,
            "goal": goal,
            "data_source": data_source,
            "success_value": success_value,
            "failure_value": failure_value,
            "algorithm_type": algorithm_type,
            "fields": fields
        }

        sfdc_client.write_to_file(json.dumps(json_obj))
        sfdc_client.create_einstein_model_package(json_obj)
        sfdc_client.deploy_package_from_deploy_dir(sf_client.connection)

        return [
            types.TextContent(
                type="text",
                text=f"Einstein Studio model '{model_name}' creation package prepared and deployment initiated."
            )
        ]
    except Exception as e:
        return [types.TextContent(
            type="text", 
            text=f"Error creating Einstein Studio model: {str(e)}"
        )]