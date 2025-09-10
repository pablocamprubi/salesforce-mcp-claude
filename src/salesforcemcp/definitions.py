import mcp.types as types

createObjectSchema = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the object to be created. Fill always a value",
        },
        "plural_name": {
            "type": "string",
            "description": "The plural name of the object to be created. Fill always a value",
        },
        "description": {
            "type": "string",
            "description": "The general description of the object purpose in a short sentence. Fill always a value",
        },
        "api_name": {
            "type": "string",
            "description": "The api name of the object to be created finished with __c",
        },
        "fields": {
            "type": "array",
            "description": "The fields of the object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["Text", "Number", "Lookup", "LongText", "Picklist", "Checkbox"],
                    "default": "Text",
                    "description": "The type of the field",
                 },
                "label": {
                    "type": "string",
                    "description": "The display name of the field",
                 },
                "api_name": {
                    "type": "string",
                    "description": "The api_name of the field finished in __c",
                 },
                "picklist_values": {
                    "type": "array",
                    "description": "The values of the field when the type is picklist",
                    "items": {"type": "string"},
                }
            },
            "additionalProperties": True,
        },
    },
    "required": ["name", "plural_name", "api_name", "description", "fields"],
}

def get_tools():
    tools = [
        # Object Creation Tools
        types.Tool(
            name="create_object",
            description="Create a new object in salesforce",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the object to be created",
                    },
                    "plural_name": {
                        "type": "string",
                        "description": "The plural name of the object to be created",
                    },
                    "description": {
                        "type": "string",
                        "description": "The general description of the object purpose in a short sentence",
                    },
                    "api_name": {
                        "type": "string",
                        "description": "The api name of the object to be created finished with __c",
                    },
                },
                "required": ["name", "plural_name", "api_name"], 
            },
        ),
        types.Tool(
            name="create_object_with_fields",
            description="Create a new object in salesforce with custom fields",
            inputSchema=createObjectSchema,
        ),
        
        # Data Query Tools
        types.Tool(
            name="run_soql_query",
            description="Executes a SOQL query against Salesforce",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SOQL query to execute (e.g., SELECT Id, Name FROM Account LIMIT 10)",
                        "examples": [
                            "SELECT Id, Name FROM Account LIMIT 10",
                            "SELECT Name, Amount FROM Opportunity WHERE CloseDate = THIS_YEAR ORDER BY Amount DESC NULLS LAST",
                            "SELECT Subject, Status, Priority FROM Case WHERE IsClosed = false",
                            "SELECT COUNT(Id) FROM Contact WHERE AccountId = '001...'"
                        ]
                    },
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="run_sosl_search",
            description="Executes a SOSL search against Salesforce",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "The SOSL search string (e.g., 'FIND {MyCompany} IN ALL FIELDS RETURNING Account(Id, Name)')",
                        "examples": [
                            "FIND {Acme} IN NAME FIELDS RETURNING Account(Name), Contact(FirstName, LastName)",
                            "FIND {support@example.com} IN EMAIL FIELDS RETURNING Contact(Name, Email)",
                            "FIND {SF*} IN ALL FIELDS LIMIT 20"
                        ]
                    },
                },
                "required": ["search"]
            }
        ),
        types.Tool(
            name="get_object_fields",
            description="Retrieves detailed information about the fields of a specific Salesforce object",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        "description": "The API name of the Salesforce object (e.g., 'Account', 'Contact', 'MyCustomObject__c')",
                        "examples": [
                            "Account",
                            "Opportunity", 
                            "Lead",
                            "My_Custom_Object__c"
                        ]
                    },
                },
                "required": ["object_name"]
            }
        ),
        types.Tool(
            name="describe_object",
            description="Get detailed schema information for a Salesforce object, including fields, relationships, and picklist values",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        "description": "API name of the object (e.g., 'Account', 'Custom_Object__c')",
                    },
                    "include_field_details": {
                        "type": "boolean",
                        "description": "Whether to include detailed field information (default: true)",
                        "default": True,
                    },
                },
                "required": ["object_name"],
            },
        ),
        
        # Einstein Studio Model Tools
        types.Tool(
            name="create_einstein_model",
            description="Create an Einstein Studio model using AppFrameworkTemplateBundle",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "The name/label of the Einstein Studio model",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the model predicts or analyzes",
                    },
                    "model_capability": {
                        "type": "string",
                        "description": "The capability of the model",
                        "enum": ["BinaryClassification", "Regression", "MultiClassification"],
                        "default": "BinaryClassification"
                    },
                    "outcome_field": {
                        "type": "string",
                        "description": "The field name that represents the outcome/target variable (e.g., 'Converted__c')",
                    },
                    "goal": {
                        "type": "string", 
                        "description": "The goal for the outcome",
                        "enum": ["Maximize", "Minimize"],
                        "default": "Maximize"
                    },
                    "data_source": {
                        "type": "string",
                        "description": "The name of the data model object to use as training data (e.g., 'Lead_Model_Training__dlm')",
                    },
                    "success_value": {
                        "type": "string",
                        "description": "The value that represents success for binary classification (e.g., 'true')",
                        "default": "true"
                    },
                    "failure_value": {
                        "type": "string", 
                        "description": "The value that represents failure for binary classification (e.g., 'false')",
                        "default": "false"
                    },
                    "algorithm_type": {
                        "type": "string",
                        "description": "The algorithm to use for the model",
                        "enum": ["XGBoost", "LinearRegression", "LogisticRegression"],
                        "default": "XGBoost"
                    },
                    "fields": {
                        "type": "array",
                        "description": "The fields to include in the model for prediction",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field_name": {
                                    "type": "string",
                                    "description": "The API name of the field",
                                },
                                "field_label": {
                                    "type": "string",
                                    "description": "The display label of the field",
                                },
                                "field_type": {
                                    "type": "string",
                                    "enum": ["Text", "Number"],
                                    "description": "The type of the field",
                                },
                                "data_type": {
                                    "type": "string", 
                                    "enum": ["Categorical", "Numerical"],
                                    "description": "How the field should be treated in the model",
                                },
                                "ignored": {
                                    "type": "boolean",
                                    "description": "Whether to ignore this field in the model",
                                    "default": False
                                }
                            },
                            "required": ["field_name", "field_label", "field_type", "data_type"]
                        }
                    }
                },
                "required": ["model_name", "description", "outcome_field", "data_source", "fields"]
            },
        ),
    ]
    
    return tools