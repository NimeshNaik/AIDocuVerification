# Document Verification Platform

AI-powered document verification system designed for Indian government services. This platform automates the extraction, validation, and fraud detection of official documents like Aadhaar, PAN, and Driver's Licenses.

## Key Features

- **Automated Verification**: Extracts text and validates ID formats automatically.
- **Fraud Detection**: Flags potential inconsistencies or tampering.
- **Image Upscaling**: Enhances low-quality document images by 4x using the **Swin2SR** model before verification.
- **Vision-Language Models**: Utilizes advanced VLMs (via OpenRouter) for intelligent document understanding.
- **Audit Logging**: Comprehensive logs of all verification requests and officer decisions.
- **MCP Server**: Can run as a Model Context Protocol server to provide verification tools to AI agents.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database & Auth**: Supabase (PostgreSQL)
- **AI Models**: 
  - **Upscaling**: Swin2SR (Transformers/PyTorch)
  - **Verification**: OpenRouter API (Qwen/Llama)
- **Tools**: Pydantic, Uvicorn

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: Vanilla CSS (Modern Design System)
- **State/Auth**: Supabase Client
- **Icons**: Lucide React

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase Account
- OpenRouter API Key

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This will install PyTorch and Transformers for the upscaling feature.*

4. **Environment Variables**:
   Create a `.env` file in the `backend/` directory:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   VLM_API_KEY=your_openrouter_api_key
   ```

5. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Environment Variables**:
   Create a `.env` file in the `frontend/` directory:
   ```env
   VITE_SUPABASE_URL=your_supabase_url
   VITE_SUPABASE_KEY=your_supabase_anon_key
   VITE_API_URL=http://localhost:8000
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```
   Access the dashboard at `http://localhost:5173`.

## API Documentation

Once the backend is running, full interactive API documentation is available:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## MCP Server (Model Context Protocol)

This backend exposes tools for AI agents (like Claude Desktop) to invoke document verification programmatically.

### Available Tools
| Tool | Description |
|------|-------------|
| `verify_document` | Verify a document image (base64) and get extraction + recommendation. |
| `validate_id_number` | Validate the format of an Indian ID number (Aadhaar, PAN, etc.). |
| `get_supported_documents` | List all document types supported by the system. |
| `upscale_document` | Upscale a low-quality document image by 4x. |

### Configuration for Claude Desktop

Add this configuration to your `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "document-verification": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/absolute/path/to/Projects/Capstone/backend"
    }
  }
}
```
*Note: Replace `/absolute/path/to/...` with your actual project path.*
