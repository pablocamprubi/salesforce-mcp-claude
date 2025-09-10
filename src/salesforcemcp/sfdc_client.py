import json
import time
import shutil
import os
import base64
import zipfile
from simple_salesforce import Salesforce
from typing import Optional, Any
import xml.etree.ElementTree as ET

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY_DIR = "deployment_package"

def _clean_deploy_dir():
    """Removes and recreates the deployment directory."""
    deploy_path = os.path.join(BASE_PATH, DEPLOY_DIR)
    if os.path.exists(deploy_path):
        shutil.rmtree(deploy_path)
    os.makedirs(deploy_path, exist_ok=True)

class OrgHandler:
    """Manages interactions and caching for a Salesforce org."""

    def __init__(self):
        self.connection: Optional[Salesforce] = None
        self.metadata_cache: dict[str, Any] = {}

    def establish_connection(self) -> bool:
        """Initiates and authenticates the connection to the Salesforce org.

        Returns:
            bool: Returns True upon successful authentication, False otherwise.
        """
        try:
            self.connection = Salesforce(
                username=os.getenv("USERNAME"),
                password=os.getenv("PASSWORD"),
                security_token=os.getenv("SECURITY_TOKEN")
            )
            return True
        except Exception as e:
            print(f"Failed to establish Salesforce connection: {str(e)}")
            self.connection = None
            return False

    def get_object_fields_cached(self, object_name: str) -> dict:
        """Retrieves and caches field information for a Salesforce object.
        
        Args:
            object_name: The API name of the Salesforce object
            
        Returns:
            dict: Field metadata for the object
            
        Raises:
            ValueError: If connection is not established or object doesn't exist
        """
        if not self.connection:
            raise ValueError("Salesforce connection not established.")
            
        # Check cache first
        if object_name in self.metadata_cache:
            return self.metadata_cache[object_name]
            
        try:
            # Get object description
            sf_object = getattr(self.connection, object_name)
            describe = sf_object.describe()
            
            # Extract field information
            fields_info = []
            for field in describe.get("fields", []):
                field_info = {
                    "name": field.get("name"),
                    "label": field.get("label"),
                    "type": field.get("type"),
                    "length": field.get("length"),
                    "required": not field.get("nillable", True),
                    "unique": field.get("unique", False),
                    "externalId": field.get("externalId", False),
                    "createable": field.get("createable", False),
                    "updateable": field.get("updateable", False),
                }
                
                # Add picklist values if applicable
                if field.get("type") in ("picklist", "multipicklist") and field.get("picklistValues"):
                    field_info["picklistValues"] = field.get("picklistValues")
                    
                # Add reference info if applicable  
                if field.get("type") == "reference" and field.get("referenceTo"):
                    field_info["referenceTo"] = field.get("referenceTo")
                    field_info["relationshipName"] = field.get("relationshipName")
                    
                fields_info.append(field_info)
            
            # Cache the result
            result = {
                "objectName": object_name,
                "fields": fields_info,
                "objectInfo": {
                    "label": describe.get("label"),
                    "labelPlural": describe.get("labelPlural"),
                    "custom": describe.get("custom", False),
                    "createable": describe.get("createable", False),
                    "updateable": describe.get("updateable", False),
                    "deletable": describe.get("deletable", False)
                }
            }
            
            self.metadata_cache[object_name] = result
            return result
            
        except AttributeError:
            raise ValueError(f"Object '{object_name}' not found or not accessible.")
        except Exception as e:
            raise ValueError(f"Error retrieving fields for {object_name}: {str(e)}")

def write_to_file(content):
    """Writes content to a log file."""
    with open(f"{BASE_PATH}/mylog.txt", 'a') as f:
        f.write(content)

def zip_directory(filepath):
    """Zips a directory."""
    source_directory = filepath
    output_zip_name = f"{BASE_PATH}/pack"
    shutil.make_archive(output_zip_name, 'zip', source_directory)

def binary_to_base64(file_path):
    """Converts a binary file to base64 encoding."""
    try:
        with open(file_path, "rb") as binary_file:
            binary_data = binary_file.read()
            base64_encoded = base64.b64encode(binary_data)
            return base64_encoded.decode('utf-8')
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

import requests

def deploy(b64, sf):
    """Deploys the zipped package using the provided simple_salesforce connection."""
    if not sf:
         print("Error: Salesforce connection object (sf) not provided to deploy function.")
         raise ValueError("Deployment failed: Invalid Salesforce connection.")

    try:
        session_id = sf.session_id
        instance_url = sf.sf_instance
        if not instance_url:
             raise ValueError("Could not retrieve instance URL from Salesforce connection.")

        metadata_api_version = "58.0" 
        endpoint = f"https://{instance_url}/services/Soap/m/{metadata_api_version}"
        print(f"Using dynamic endpoint: {endpoint}")
    except AttributeError as e:
         print(f"Error accessing connection attributes: {e}")
         raise ValueError("Deployment failed: Could not get session details from Salesforce connection.")

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        'SOAPAction': '""'
    }

    xml_body_template = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:met="http://soap.sforce.com/2006/04/metadata">
   <soapenv:Header>
      <met:SessionHeader>
         <met:sessionId>{session_id}</met:sessionId>
      </met:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <met:deploy>
         <met:ZipFile>{base64_zip}</met:ZipFile>
         <met:DeployOptions>
            <met:allowMissingFiles>false</met:allowMissingFiles>
            <met:autoUpdatePackage>false</met:autoUpdatePackage>
            <met:checkOnly>false</met:checkOnly>
            <met:ignoreWarnings>false</met:ignoreWarnings>
            <met:performRetrieve>false</met:performRetrieve>
            <met:purgeOnDelete>false</met:purgeOnDelete>
            <met:rollbackOnError>true</met:rollbackOnError>
            <met:singlePackage>true</met:singlePackage>
         </met:DeployOptions>
      </met:deploy>
   </soapenv:Body>
</soapenv:Envelope>
    """

    if b64 is None:
        print("Error: Base64 package data is None. Cannot deploy.")
        raise ValueError("Deployment failed: Invalid package data.")

    xml_body = xml_body_template.format(session_id=session_id, base64_zip=b64)

    with open(f"{BASE_PATH}/deploy.log", "w", encoding="utf-8") as file:
        file.write(xml_body)

    try:
        response = requests.post(endpoint, data=xml_body, headers=headers)
        
        print(f"Deployment API Response Status: {response.status_code}")
        print(f"Deployment API Response Text:\n{response.text}")
        with open(f"{BASE_PATH}/deploy_http.log", "w", encoding="utf-8") as file:
            file.write(response.text)

        if response.status_code >= 400:
             fault_message = f"HTTP Error {response.status_code}."
             try:
                 root = ET.fromstring(response.text)
                 fault = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
                 if fault is not None:
                     faultcode = fault.findtext('{*}faultcode')
                     faultstring = fault.findtext('{*}faultstring')
                     fault_message = f"SOAP Fault: Code='{faultcode}', Message='{faultstring}' (HTTP Status: {response.status_code})"
             except ET.ParseError:
                 fault_message += " Additionally, the response body was not valid XML."
             except Exception as parse_e:
                 print(f"Minor error parsing SOAP fault: {parse_e}")
                 fault_message += f" Response Text: {response.text[:500]}..."
             
             raise ValueError(f"Salesforce deployment API call failed: {fault_message}")
        print("Deployment request submitted successfully to Salesforce.")

    except requests.exceptions.RequestException as req_e:
         print(f"Network error during deployment API call: {req_e}")
         raise ValueError(f"Deployment failed: Network error contacting Salesforce API. Details: {str(req_e)}")
    except Exception as e:
        print(f"Unexpected error during deployment call: {e}")
        raise

def create_send_to_server(sf):
    """Zips the current package and sends it for deployment using the provided sf connection."""
    zip_directory(f"{BASE_PATH}/current")
    b64 = binary_to_base64(f"{BASE_PATH}/pack.zip")
    deploy(b64, sf)

def create_metadata_package(json_obj):
    """Creates a metadata package for custom object creation with fields."""
    try:
        name = json_obj["name"]
        plural_name = json_obj["plural_name"]
        description = json_obj["description"]
        api_name = json_obj["api_name"]
        fields = json_obj["fields"]

        try:
            shutil.rmtree(f"{BASE_PATH}/current/")
        except:
            print("the current directory doesn't exist")

        source = f"{BASE_PATH}/assets/create_object_tmpl/"
        destination = f"{BASE_PATH}/current/"

        shutil.copytree(source, destination)

        old_name = f"{BASE_PATH}/current/objects/##api_name##.object"
        new_name = f"{BASE_PATH}/current/objects/{api_name}.object"

        os.rename(old_name, new_name)

        with open(f"{BASE_PATH}/assets/field.tmpl", "r", encoding="utf-8") as file:
            field_tmpl = file.read()

        fields_str = ""
        field_names = []

        for field in fields:
            type_def = ""

            f_name = field["label"]
            f_type = field["type"]
            f_api_name = field["api_name"]
            field_names.append(f_api_name)

            if f_type == "Text":
                type_def = """<type>Text</type>\n                    <length>100</length>"""
            elif f_type == "URL":
                type_def = "<type>Url</type>"
            elif f_type == "Checkbox":
                default_val = field.get("defaultValue", False)
                type_def = f"<type>Checkbox</type>\n                    <defaultValue>{str(default_val).lower()}</defaultValue>"
            elif f_type == "Lookup":
                reference_to = field.get("referenceTo", "")
                relationship_label = field.get("relationshipLabel", "")
                relationship_name = field.get("relationshipName", "")
                type_def = f"<type>Lookup</type>\n                    <referenceTo>{reference_to}</referenceTo>"
                if relationship_label:
                    type_def += f"\n                    <relationshipLabel>{relationship_label}</relationshipLabel>"
                if relationship_name:
                    type_def += f"\n                    <relationshipName>{relationship_name}</relationshipName>"
            else:
                if f_type == "Picklist":
                    f_picklist_values = field["picklist_values"]
                    picklist_values_str = ""
                    for picklist_value in f_picklist_values:
                        val = f"""<value>
                                    <fullName>{picklist_value}</fullName>
                                    <default>false</default>
                                    <label>{picklist_value}</label>
                                </value>
                                """
                        picklist_values_str = picklist_values_str + val

                    type_def = f"""
                        <type>Picklist</type>
                        <valueSet>
                            <restricted>true</restricted>
                            <valueSetDefinition>
                                <sorted>false</sorted>
                                {picklist_values_str}
                            </valueSetDefinition>
                        </valueSet>
                        """
                else:
                    type_def = """<precision>18</precision>
                        <scale>0</scale>
                        <type>Number</type>"""

            new_field = field_tmpl.replace("##api_name##", f_api_name)
            new_field = new_field.replace("##name##", f_name)
            new_field = new_field.replace("##type##", type_def)
            fields_str = fields_str + new_field

        # Update package.xml to include both object and profile
        package_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>{api_name}</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Admin</members>
        <name>Profile</name>
    </types>
    <version>63.0</version>
</Package>""".format(api_name=api_name)

        with open(f"{BASE_PATH}/current/package.xml", "w", encoding="utf-8") as file:
            file.write(package_xml)

        obj_path = f"{BASE_PATH}/current/objects/{api_name}.object"

        with open(obj_path, "r", encoding="utf-8") as file:
            obj_tmpl = file.read()

        if description is None:
            description = ""

        obj_tmpl = obj_tmpl.replace("##description##", description)
        obj_tmpl = obj_tmpl.replace("##name##", name)
        obj_tmpl = obj_tmpl.replace("##plural_name##", plural_name)
        obj_tmpl = obj_tmpl.replace("##fields##", fields_str)

        with open(obj_path, "w", encoding="utf-8") as file:
            file.write(obj_tmpl)

        # Create profiles directory in the deployment package
        profiles_dir = os.path.join(f"{BASE_PATH}/current", "profiles")
        os.makedirs(profiles_dir, exist_ok=True)

        # Create field permissions XML
        field_permissions = ""
        for field in field_names:
            field_permissions += f"""    <fieldPermissions>
        <editable>true</editable>
        <field>{api_name}.{field}</field>
        <readable>true</readable>
    </fieldPermissions>
"""

        # Create profile XML using template
        with open(os.path.join(BASE_PATH, "assets", "profile.tmpl"), "r", encoding="utf-8") as f:
            profile_template = f.read()

        profile_xml = profile_template.replace("##fieldPermissions##", field_permissions)

        # Write profile XML
        with open(os.path.join(profiles_dir, "Admin.profile"), "w", encoding="utf-8") as f:
            f.write(profile_xml)

    except Exception as e:
        err_msg = f"An error occurred: {e}"
        with open(f"{BASE_PATH}/check.txt", 'a') as f:
            f.write(err_msg)

def create_einstein_model_package(json_obj):
    """Creates an Einstein Studio model package using AppFrameworkTemplateBundle."""
    try:
        # Clean and prepare deploy directory
        _clean_deploy_dir()
        
        model_name = json_obj["model_name"]
        description = json_obj["description"]
        model_capability = json_obj["model_capability"]
        outcome_field = json_obj["outcome_field"]
        goal = json_obj["goal"]
        data_source = json_obj["data_source"]
        success_value = json_obj["success_value"]
        failure_value = json_obj["failure_value"]
        algorithm_type = json_obj["algorithm_type"]
        fields = json_obj["fields"]
        
        # Create template name (sanitized)
        template_name = model_name.replace(" ", "_").replace("-", "_")
        
        # Copy Einstein model template structure
        source_template = os.path.join(BASE_PATH, "assets", "create_einstein_model_tmpl", "appTemplates", "##template_name##")
        deploy_dir = os.path.join(BASE_PATH, DEPLOY_DIR)
        target_template_dir = os.path.join(deploy_dir, "appTemplates", template_name)
        
        # Create directory structure
        os.makedirs(target_template_dir, exist_ok=True)
        
        # Copy and process template files
        shutil.copytree(source_template, target_template_dir, dirs_exist_ok=True)
        
        # Process ModelContainer.json
        container_path = os.path.join(target_template_dir, "ml", "containers", "ModelContainer.json")
        with open(container_path, "r", encoding="utf-8") as f:
            container_content = f.read()
        
        container_content = container_content.replace("##model_label##", model_name)
        container_content = container_content.replace("##model_description##", description)
        container_content = container_content.replace("##model_capability##", model_capability)
        container_content = container_content.replace("##outcome_field##", outcome_field)
        container_content = container_content.replace("##goal##", goal)
        
        with open(container_path, "w", encoding="utf-8") as f:
            f.write(container_content)
        
        # Process ModelSetup.json with fields
        setup_path = os.path.join(target_template_dir, "ml", "setups", "ModelSetup.json")
        with open(setup_path, "r", encoding="utf-8") as f:
            setup_content = f.read()
        
        # Build fields JSON
        fields_json = build_einstein_fields_json(fields, outcome_field)
        
        # Determine outcome type based on model capability
        outcome_type = "Binary" if model_capability == "BinaryClassification" else "Regression"
        
        setup_content = setup_content.replace("##setup_description##", f"{description} - Model Setup")
        setup_content = setup_content.replace("##data_source##", data_source)
        setup_content = setup_content.replace("##outcome_type##", outcome_type)
        setup_content = setup_content.replace("##failure_value##", failure_value)
        setup_content = setup_content.replace("##goal##", goal)
        setup_content = setup_content.replace("##outcome_label##", outcome_field.replace("_", " ").replace("__c", ""))
        setup_content = setup_content.replace("##outcome_field##", outcome_field)
        setup_content = setup_content.replace("##success_value##", success_value)
        setup_content = setup_content.replace("##algorithm_type##", algorithm_type)
        setup_content = setup_content.replace("##fields_json##", fields_json)
        
        with open(setup_path, "w", encoding="utf-8") as f:
            f.write(setup_content)
        
        # Process template-info.json
        template_info_path = os.path.join(target_template_dir, "template-info.json")
        with open(template_info_path, "r", encoding="utf-8") as f:
            template_info_content = f.read()
        
        template_info_content = template_info_content.replace("##model_label##", model_name)
        template_info_content = template_info_content.replace("##template_description##", f"{description} - Einstein Studio Model Template")
        template_info_content = template_info_content.replace("##template_name##", template_name)
        
        with open(template_info_path, "w", encoding="utf-8") as f:
            f.write(template_info_content)
        
        # Create package.xml for AppFrameworkTemplateBundle
        source_package = os.path.join(BASE_PATH, "assets", "create_einstein_model_tmpl", "package.xml")
        target_package = os.path.join(deploy_dir, "package.xml")
        
        with open(source_package, "r", encoding="utf-8") as f:
            package_content = f.read()
        
        package_content = package_content.replace("##template_name##", template_name)
        
        with open(target_package, "w", encoding="utf-8") as f:
            f.write(package_content)
        
        write_to_file(f"Einstein Studio model package created: {template_name}")
        
    except Exception as e:
        err_msg = f"Error creating Einstein model package: {e}"
        with open(f"{BASE_PATH}/check.txt", 'a') as f:
            f.write(err_msg)
        raise Exception(err_msg)

def build_einstein_fields_json(fields, outcome_field):
    """Builds the fields JSON array for Einstein Studio ModelSetup."""
    try:
        fields_array = []
        
        # Add outcome field first (always Text/Categorical for classification)
        outcome_field_obj = {
            "type": "Text",
            "balanced": False,
            "dataType": "Categorical",
            "highCardinality": False,
            "ignored": False,
            "includeOther": True,
            "label": outcome_field.replace("_", " ").replace("__c", ""),
            "name": outcome_field,
            "ordering": "Occurrence",
            "sensitive": False,
            "source": None,
            "values": []
        }
        fields_array.append(outcome_field_obj)
        
        # Add other fields with correct structure per field type
        for field in fields:
            field_name = field["field_name"]
            field_label = field["field_label"] 
            field_type = field["field_type"]
            data_type = field["data_type"]
            ignored = field.get("ignored", False)
            
            if field_type == "Text":
                # Text fields structure
                field_obj = {
                    "type": "Text",
                    "balanced": False,
                    "dataType": data_type,
                    "highCardinality": False,
                    "ignored": ignored,
                    "includeOther": True,
                    "label": field_label,
                    "name": field_name,
                    "ordering": "Occurrence",
                    "sensitive": False,
                    "source": None,
                    "values": []
                }
            elif field_type == "Number":
                # Number fields structure (different properties)
                field_obj = {
                    "type": "Number",
                    "bucketingStrategy": {
                        "type": "Percentile",
                        "numberOfBuckets": 10
                    },
                    "highCardinality": None,
                    "ignored": ignored,
                    "label": field_label,
                    "name": field_name,
                    "sensitive": False,
                    "source": None,
                    "max": 10000000000,
                    "min": 0
                }
            else:
                # Fallback to Text structure for unknown types
                field_obj = {
                    "type": "Text",
                    "balanced": False,
                    "dataType": "Categorical",
                    "highCardinality": False,
                    "ignored": ignored,
                    "includeOther": True,
                    "label": field_label,
                    "name": field_name,
                    "ordering": "Occurrence",
                    "sensitive": False,
                    "source": None,
                    "values": []
                }
            
            fields_array.append(field_obj)
        
        return json.dumps(fields_array, indent=4)
        
    except Exception as e:
        raise Exception(f"Error building fields JSON: {e}")

def deploy_package_from_deploy_dir(sf):
    """Zips the DEPLOY_DIR and deploys it via the Metadata API."""
    deploy_dir_path = os.path.join(BASE_PATH, DEPLOY_DIR)
    if not os.path.exists(deploy_dir_path):
        raise FileNotFoundError(f"Deployment directory not found: {deploy_dir_path}")

    # Zip only the contents of the deployment directory (no parent folder)
    zip_path = os.path.join(BASE_PATH, "deploy_package.zip")
    # Remove old zip if present
    if os.path.exists(zip_path):
        os.remove(zip_path)
    # Create new zip with contents at the root
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(deploy_dir_path):
            for file in files:
                abs_file = os.path.join(root, file)
                # Compute path relative to deploy_dir_path
                rel_path = os.path.relpath(abs_file, deploy_dir_path)
                zf.write(abs_file, rel_path)

    # Encode and deploy
    b64 = binary_to_base64(zip_path)
    deploy(b64, sf)