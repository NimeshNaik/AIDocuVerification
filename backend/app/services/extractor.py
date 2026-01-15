"""
VLM-based document field extraction service.
Uses OpenRouter API with Qwen2.5-VL for document analysis.
"""
import base64
import json
import httpx
from typing import Dict, Any

from app.core.config import get_settings

settings = get_settings()

# System prompt for document extraction
EXTRACTION_PROMPT = """You are an expert government document verification specialist. 
Your task is to analyze Indian government ID documents for authenticity, extract specific information, and detect potential fraud.

**PART 1: DOCUMENT VALIDATION**
First, determine if this image is a valid Indian Government ID document (Aadhaar, PAN, Voter ID, Driving License, Passport, Birth Certificate).
If the image is NOT an Indian Government ID (e.g., random object, scenery, animal, non-ID document), mark `is_indian_government_id` as `false` and provide a reason.

**PART 2: FORENSIC ANALYSIS & FRAUD DETECTION**
Critically analyze the document for detailed fraud indicators. You must Reason about the document's validity.
Check for the following speicifcally:
1. **Consistency**: Do fonts, sizes, and alignment look official? Are there mixed scripts?
2. **Alterations**: Look for digital edits, blurriness around text, mismatched pixel density, or "copy-paste" artifacts.
3. **Security Features**: Identify official seals, holograms, stamps, and signatures.
4. **Logic Check**: Is the document "too good to be true"? (e.g., perfect digital generation vs scanned photo).
5. **Physical Anomalies**: Look for torn edges, shadows, or lighting that suggest a real physical card vs a digital screenshot.
6. **Person's photo**: Is the photo of the person in document an photo of an actual person? If the photo is not proper or not visible, mark it as suspicious.

**PART 3: EXTRACTION**
Extract the following fields from the document.
**IMPORTANT: Regional Language Handling**
- If the document contains text in local regional Indian languages (e.g., Hindi, Kannada, Tamil, etc.), you MUST translate/transliterate it into English.
- Ensure all extracted names and addresses are in English characters.

Extract:
1. Document Type (aadhaar, pan, voter_id, driving_license, passport, birth_certificate, or unknown)
2. Full Name (as written on the document, English only)
3. Date of Birth (DD-MM-YYYY format preferred)
4. ID Number (the primary unique identifier)
5. Any other information that is available on the document in label value pairs



**OUTPUT FORMAT**
Return a SINGLE JSON object with this exact structure:
{
    "is_indian_government_id": true/false,
    "rejection_reason": "Reason if not a valid ID, null otherwise",
    "document_type": "string",
    "confidence": 0.0-1.0,
    "fields": {
        "name": {"value": "string", "confidence": 0.0-1.0},
        "dob": {"value": "string", "confidence": 0.0-1.0},
        "id_number": {"value": "string", "confidence": 0.0-1.0},
        "address": {"value": "string", "confidence": 0.0-1.0}
    },
    "fraud_analysis": {
        "is_genuine_appearance": true,
        "validity_score": 0.0-1.0,
        "reasoning": "Detailed explanation of your judgment. Discuss seals, fonts, and consistency.",
        "suspicious_elements": ["List specific suspicious things e.g., 'Wrong font for Aadhaar', 'Blurry photo area'"],
        "alterations_detected": ["List specific signs of digital tampering e.g., 'Pixelated text block', 'Mismatched background'"],
        "security_features_found": ["List features found e.g., 'Government Hologram', 'QR Code', 'Stamp'"]
    },
    "issues": ["List of general quality issues e.g. 'Low resolution', 'Glare'"],
    "is_readable": true
}

If the document is unreadable, set "is_readable": false.
Be extremely strict with "validity_score". A generic digital template should score low (<0.5). A real photo of a card should score high (>0.8).
"""


async def extract_fields_openrouter(image_bytes: bytes, content_type: str) -> Dict[str, Any]:
    """
    Extract fields using OpenRouter API with Qwen2.5-VL model.
    
    Args:
        image_bytes: Raw image bytes
        content_type: MIME type of the image
    
    Returns:
        Extracted fields with confidence scores
    """
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    # Determine media type
    if content_type in ["image/jpeg", "image/jpg"]:
        media_type = "image/jpeg"
    elif content_type == "image/png":
        media_type = "image/png"
    else:
        media_type = "image/jpeg"  # Default fallback
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.vlm_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://document-verification-platform.local",
                "X-Title": "Document Verification Platform"
            },
            json={
                "model": settings.vlm_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": EXTRACTION_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 15000,
                "temperature": 0.1
            },
            timeout=60.0  # Longer timeout for vision models
        )

        if response.status_code != 200:
            error_detail = response.text
            raise Exception(f"OpenRouter API error ({response.status_code}): {error_detail}")
        
        result = response.json()
        
        # Check for API errors in response
        if "error" in result:
            raise Exception(f"OpenRouter API error: {result['error']}")
        
        text_response = result["choices"][0]["message"]["content"]
        
        # Parse JSON from response (handle markdown code blocks)
        if "```json" in text_response:
            json_str = text_response.split("```json")[1].split("```")[0].strip()
        elif "```" in text_response:
            json_str = text_response.split("```")[1].split("```")[0].strip()
        else:
            json_str = text_response.strip()
        
        return json.loads(json_str)


async def extract_fields(image_bytes: bytes, content_type: str) -> Dict[str, Any]:
    """
    Extract fields from document image using configured VLM provider.
    
    Args:
        image_bytes: Raw image bytes
        content_type: MIME type of the image
    
    Returns:
        Extracted fields with confidence scores
    """
    if settings.vlm_provider.lower() == "openrouter":
        return await extract_fields_openrouter(image_bytes, content_type)
    else:
        raise ValueError(f"Unsupported VLM provider: {settings.vlm_provider}. Use 'openrouter' for Qwen2.5-VL.")
