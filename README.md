# Salesforce MCP Connector - Simplified Edition 🚀

**Must read -**
**This is not an official Salesforce repository.**

Welcome to the simplified Salesforce Model Context Protocol server! 
This MCP allows you to create custom objects and query data in your Salesforce org using natural language.

This repository has been cleaned and simplified to focus on **object creation, data querying, and Einstein Studio model functionality**. 
If you need the full feature set, please visit the original repository.

## What You Can Do ✨

### **Create Custom Objects** 🛠️
- Create new custom objects in your Salesforce org
- Add custom fields to your objects during creation
- Examples:
  - "Create a new custom object named 'Product' with fields for name, price, and category"
  - "Create a 'Contract' object with text, number, and picklist fields"

### **Query Your Data** 🔍
- Execute SOQL queries to retrieve records from your Salesforce org
- Search across multiple objects using SOSL
- Explore object schemas and field definitions
- Get detailed information about your Salesforce objects
- Examples:
  - "Show me all accounts created this year with their annual revenue"
  - "What fields are available on the Contact object?"
  - "Search for all records containing 'Acme' across the org"
  - "Describe the Account object structure"

### **Create Einstein Studio Models** 🤖
- Create predictive machine learning models using Einstein Studio
- Configure model capabilities like binary classification and regression
- Define outcome fields and prediction goals
- Specify training data sources and model fields
- Examples:
  - "Create a lead conversion prediction model using XGBoost algorithm"
  - "Build a sales opportunity forecasting model with regression capability"
  - "Create a customer churn prediction model with specific data fields"

## Quick Start ⚡

### Local Installation

First install the server:

```sh
git clone <this-repository>
cd salesforce-mcp
uv venv
uv pip install -e .
```

Then, configure it in your `claude_desktop_config.json` file:

```json
{
    "mcpServers": {
        "salesforce": {
            "command": "uv",
            "args": [
                "--directory",
                "[REPO_CLONE_PATH]/salesforce-mcp/src",
                "run",
                "server.py"
            ],
            "env": {
                "USERNAME": "YOUR_SALESFORCE_USERNAME",
                "PASSWORD": "YOUR_SALESFORCE_PASSWORD",
                "SECURITY_TOKEN": "YOUR_SALESFORCE_SECURITY_TOKEN"
            }
        }
    }
}
```

Replace the placeholder values with your Salesforce credentials:
- `YOUR_SALESFORCE_USERNAME`: Your Salesforce username
- `YOUR_SALESFORCE_PASSWORD`: Your Salesforce password
- `YOUR_SALESFORCE_SECURITY_TOKEN`: Your Salesforce security token

## Supported Functions 📥

### Object Creation Functions
| Tool Name                | Description                                                                 | Required Input Fields                                  | Active |
|--------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------|--------|
| create_object            | Create a new object in Salesforce                                           | name, plural_name, api_name                            | ✅     |
| create_object_with_fields| Create a new object in Salesforce with custom fields                        | name, plural_name, api_name, description, fields       | ✅     |

### Data Query Functions
| Tool Name                | Description                                                                 | Required Input Fields                                  | Active |
|--------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------|--------|
| run_soql_query           | Execute a SOQL query against Salesforce                                     | query                                                  | ✅     |
| run_sosl_search          | Execute a SOSL search across multiple objects                               | search                                                 | ✅     |
| get_object_fields        | Get detailed field information for a Salesforce object                      | object_name                                            | ✅     |
| describe_object          | Get comprehensive schema information for an object (markdown format)        | object_name, include_field_details (optional)          | ✅     |

### Einstein Studio Model Functions
| Tool Name                | Description                                                                 | Required Input Fields                                  | Active |
|--------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------|--------|
| create_einstein_model    | Create an Einstein Studio predictive model using AppFrameworkTemplateBundle| model_name, description, outcome_field, data_source, fields | ✅     |

## Field Types Supported

When creating objects with fields, you can use the following field types:
- **Text** - Standard text field
- **Number** - Numeric field with precision and scale
- **Checkbox** - Boolean field
- **Picklist** - Dropdown field with predefined values
- **Lookup** - Reference to another object

## Einstein Studio Model Configuration

When creating Einstein Studio models, you can specify:
- **Model Capabilities**: BinaryClassification, Regression, MultiClassification
- **Algorithms**: XGBoost, LinearRegression, LogisticRegression  
- **Field Types**: Text (Categorical), Number (Numerical)
- **Goals**: Maximize or Minimize the outcome
- **Training Data**: Reference to your Data Cloud model object

## Examples

### Simple Object Creation
```
"Create a custom object called 'Vehicle' with plural name 'Vehicles'"
```

### Object with Fields
```
"Create a 'Product' object with the following fields:
- Name (Text)
- Price (Number) 
- Category (Picklist with values: Electronics, Clothing, Books)
- Active (Checkbox)"
```

### Data Queries
```
"Show me the first 10 accounts with their names and annual revenue"
→ Uses: SELECT Id, Name, AnnualRevenue FROM Account LIMIT 10

"What fields are available on the Opportunity object?"
→ Uses: get_object_fields with object_name: "Opportunity"

"Search for all records containing 'Technology'"
→ Uses: FIND {Technology} IN ALL FIELDS RETURNING Account(Name), Contact(Name)

"Describe the Contact object structure"
→ Uses: describe_object with detailed field information
```

### Einstein Studio Models
```
"Create a lead conversion prediction model called 'Lead Scoring Model'"
→ Creates: Einstein Studio model with binary classification capability

"Build a sales forecasting model using opportunity data"
→ Creates: Regression model for predicting sales amounts

"Create a customer churn prediction model with the following fields:
- Account_Value__c (Number/Numerical)
- Industry__c (Text/Categorical)  
- Last_Activity_Date__c (Text/Categorical)
- Outcome: Churned__c"
→ Creates: Complete Einstein Studio model with specified configuration
```

## Security Note 🔒

Your Salesforce credentials are stored securely and are only used to establish the connection to your org. 
We never store or share your credentials with third parties.

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.