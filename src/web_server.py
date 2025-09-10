#!/usr/bin/env python3
"""
HTTP API wrapper for Salesforce MCP server.
Exposes MCP tools as REST API endpoints for ChatGPT and web usage.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import uvicorn

# Import your existing MCP components
from salesforcemcp import sfdc_client
from salesforcemcp import implementations as sfmcpimpl

app = FastAPI(
    title="Salesforce MCP API",
    description="REST API for Salesforce operations including object creation, data querying, and Einstein Studio models",
    version="1.0.0"
)

# Initialize Salesforce client
sf_client = sfdc_client.OrgHandler()

@app.on_event("startup")
async def startup_event():
    """Initialize Salesforce connection on startup"""
    if not sf_client.establish_connection():
        print("Warning: Failed to establish Salesforce connection")

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment"""
    return {"status": "healthy", "service": "Salesforce MCP API"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Salesforce MCP API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Request/Response models
class CreateObjectRequest(BaseModel):
    name: str
    plural_name: str
    api_name: str
    description: Optional[str] = None

class FieldDefinition(BaseModel):
    type: str
    label: str
    api_name: str
    picklist_values: Optional[List[str]] = None

class CreateObjectWithFieldsRequest(BaseModel):
    name: str
    plural_name: str
    api_name: str
    description: str
    fields: List[FieldDefinition]

class SOQLQueryRequest(BaseModel):
    query: str

class SOSLSearchRequest(BaseModel):
    search: str

class GetObjectFieldsRequest(BaseModel):
    object_name: str

class DescribeObjectRequest(BaseModel):
    object_name: str
    include_field_details: Optional[bool] = True

class ModelField(BaseModel):
    field_name: str
    field_label: str
    field_type: str
    data_type: str
    ignored: Optional[bool] = False

class CreateEinsteinModelRequest(BaseModel):
    model_name: str
    description: str
    model_capability: Optional[str] = "BinaryClassification"
    outcome_field: str
    goal: Optional[str] = "Maximize"
    data_source: str
    success_value: Optional[str] = "true"
    failure_value: Optional[str] = "false"
    algorithm_type: Optional[str] = "XGBoost"
    fields: List[ModelField]

# API Endpoints
@app.post("/api/create-object")
async def create_object(request: CreateObjectRequest):
    """Create a new custom object in Salesforce"""
    try:
        arguments = {
            "name": request.name,
            "plural_name": request.plural_name,
            "api_name": request.api_name,
            "description": request.description or f"Custom object: {request.name}"
        }
        result = sfmcpimpl.create_object_impl(sf_client, arguments)
        return {"success": True, "result": [r.text for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-object-with-fields")
async def create_object_with_fields(request: CreateObjectWithFieldsRequest):
    """Create a new custom object with fields in Salesforce"""
    try:
        arguments = {
            "name": request.name,
            "plural_name": request.plural_name,
            "api_name": request.api_name,
            "description": request.description,
            "fields": [field.dict() for field in request.fields]
        }
        result = sfmcpimpl.create_object_with_fields_impl(sf_client, arguments)
        return {"success": True, "result": [r.text for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/soql-query")
async def run_soql_query(request: SOQLQueryRequest):
    """Execute a SOQL query against Salesforce"""
    try:
        arguments = {"query": request.query}
        result = sfmcpimpl.run_soql_query_impl(sf_client, arguments)
        return {"success": True, "result": [r.text for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sosl-search")
async def run_sosl_search(request: SOSLSearchRequest):
    """Execute a SOSL search against Salesforce"""
    try:
        arguments = {"search": request.search}
        result = sfmcpimpl.run_sosl_search_impl(sf_client, arguments)
        return {"success": True, "result": [r.text for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/get-object-fields")
async def get_object_fields(request: GetObjectFieldsRequest):
    """Get detailed field information for a Salesforce object"""
    try:
        arguments = {"object_name": request.object_name}
        result = sfmcpimpl.get_object_fields_impl(sf_client, arguments)
        return {"success": True, "result": [r.text for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/describe-object")
async def describe_object(request: DescribeObjectRequest):
    """Get comprehensive schema information for a Salesforce object"""
    try:
        arguments = {
            "object_name": request.object_name,
            "include_field_details": request.include_field_details
        }
        result = sfmcpimpl.describe_object_impl(sf_client, arguments)
        return {"success": True, "result": [r.text for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-einstein-model")
async def create_einstein_model(request: CreateEinsteinModelRequest):
    """Create an Einstein Studio predictive model"""
    try:
        arguments = {
            "model_name": request.model_name,
            "description": request.description,
            "model_capability": request.model_capability,
            "outcome_field": request.outcome_field,
            "goal": request.goal,
            "data_source": request.data_source,
            "success_value": request.success_value,
            "failure_value": request.failure_value,
            "algorithm_type": request.algorithm_type,
            "fields": [field.dict() for field in request.fields]
        }
        result = sfmcpimpl.create_einstein_model_impl(sf_client, arguments)
        return {"success": True, "result": [r.text for r in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
