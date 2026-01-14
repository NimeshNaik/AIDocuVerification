"""
MCP (Model Context Protocol) Server for Document Verification Platform.

This module exposes document verification capabilities as MCP tools,
allowing AI assistants to verify documents programmatically.

Run with: python -m app.mcp_server
Or use with MCP client configuration.
"""
import asyncio
import base64
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import our services
from app.services.pipeline import run_verification_pipeline
from app.services.validator import validate_fields
from app.schemas.document import DocumentType

# Create MCP server instance
server = Server("document-verification")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="verify_document",
            description="""Verify an Indian government ID document (Aadhaar, PAN, Voter ID, etc.).
            
Analyzes the document image to:
- Detect document type
- Extract fields (name, DOB, ID number)
- Validate field formats
- Check for potential fraud signals
- Provide a recommendation (APPROVE/REVIEW/REJECT)

Input: Base64-encoded image of the document
Output: Verification result with extracted fields and recommendation""",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_base64": {
                        "type": "string",
                        "description": "Base64-encoded image of the document (JPEG or PNG)"
                    },
                    "image_type": {
                        "type": "string",
                        "enum": ["image/jpeg", "image/png"],
                        "description": "MIME type of the image",
                        "default": "image/jpeg"
                    },
                    "document_type_hint": {
                        "type": "string",
                        "enum": ["aadhaar", "pan", "voter_id", "driving_license", "passport"],
                        "description": "Optional hint for document type if known"
                    }
                },
                "required": ["image_base64"]
            }
        ),
        Tool(
            name="validate_id_number",
            description="""Validate an Indian ID number format without an image.
            
Checks if the provided ID number matches the expected format for:
- Aadhaar: 12 digits
- PAN: ABCDE1234F format
- Voter ID: 3 letters + 7 digits

Returns validation result with any errors found.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "id_type": {
                        "type": "string",
                        "enum": ["aadhaar", "pan", "voter_id"],
                        "description": "Type of ID to validate"
                    },
                    "id_number": {
                        "type": "string",
                        "description": "The ID number to validate"
                    }
                },
                "required": ["id_type", "id_number"]
            }
        ),
        Tool(
            name="get_supported_documents",
            description="Get list of supported document types for verification.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle MCP tool calls."""
    
    if name == "verify_document":
        return await handle_verify_document(arguments)
    
    elif name == "validate_id_number":
        return await handle_validate_id_number(arguments)
    
    elif name == "get_supported_documents":
        return await handle_get_supported_documents()
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]


async def handle_verify_document(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle document verification tool call."""
    try:
        image_base64 = arguments.get("image_base64", "")
        image_type = arguments.get("image_type", "image/jpeg")
        document_type_hint = arguments.get("document_type_hint")
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Invalid base64 image: {str(e)}"
                })
            )]
        
        # Generate a request ID for this verification
        import uuid
        request_id = str(uuid.uuid4())
        
        # Run verification pipeline
        result = await run_verification_pipeline(
            request_id=request_id,
            file_content=image_bytes,
            file_name="mcp_upload.jpg",
            content_type=image_type,
            document_type_hint=document_type_hint
        )
        
        # Convert to JSON-serializable format
        response = {
            "success": True,
            "request_id": result.request_id,
            "document_type": result.document_type.value,
            "confidence_score": result.confidence_score,
            "fields": {
                k: {"value": v.value, "confidence": v.confidence}
                for k, v in result.fields.items()
            },
            "validation_errors": result.validation_errors,
            "fraud_signals": [
                {"type": s.type, "description": s.description, "severity": s.severity}
                for s in result.fraud_signals
            ],
            "recommendation": result.recommendation.value,
            "explanation": result.explanation
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            })
        )]


async def handle_validate_id_number(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle ID number validation tool call."""
    try:
        id_type = arguments.get("id_type", "").lower()
        id_number = arguments.get("id_number", "")
        
        # Map to DocumentType
        type_mapping = {
            "aadhaar": DocumentType.AADHAAR,
            "pan": DocumentType.PAN,
            "voter_id": DocumentType.VOTER_ID
        }
        
        if id_type not in type_mapping:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "valid": False,
                    "errors": [f"Unsupported ID type: {id_type}"]
                })
            )]
        
        doc_type = type_mapping[id_type]
        
        # Create mock fields structure for validation
        fields = {
            "id_number": {"value": id_number, "confidence": 1.0}
        }
        
        errors = validate_fields(doc_type, fields)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "valid": len(errors) == 0,
                "id_type": id_type,
                "id_number": id_number,
                "errors": errors
            }, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "valid": False,
                "error": str(e)
            })
        )]


async def handle_get_supported_documents() -> list[TextContent]:
    """Return list of supported document types."""
    documents = [
        {
            "type": "aadhaar",
            "name": "Aadhaar Card",
            "description": "12-digit unique identification number issued by UIDAI",
            "fields_extracted": ["name", "dob", "id_number", "address", "gender"]
        },
        {
            "type": "pan",
            "name": "PAN Card",
            "description": "10-character alphanumeric ID for income tax",
            "fields_extracted": ["name", "dob", "id_number", "father_name"]
        },
        {
            "type": "voter_id",
            "name": "Voter ID (EPIC)",
            "description": "Electoral Photo Identity Card",
            "fields_extracted": ["name", "dob", "id_number", "address", "father_name"]
        },
        {
            "type": "driving_license",
            "name": "Driving License",
            "description": "License to drive motor vehicles",
            "fields_extracted": ["name", "dob", "id_number", "address", "validity"]
        },
        {
            "type": "passport",
            "name": "Indian Passport",
            "description": "International travel document",
            "fields_extracted": ["name", "dob", "id_number", "nationality", "validity"]
        }
    ]
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "supported_documents": documents,
            "total": len(documents)
        }, indent=2)
    )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
