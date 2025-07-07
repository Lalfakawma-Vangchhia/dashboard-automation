# Backend Scripts

This directory contains utility scripts for setting up and configuring the Automation Dashboard backend.

## Available Scripts

### `setup_stability_ai.py`
A setup script for configuring Stability AI image generation.

**Usage:**
```bash
# From the backend directory
python scripts/setup_stability_ai.py <YOUR_STABILITY_API_KEY>
```

**What it does:**
- Sets the `STABILITY_API_KEY` environment variable
- Tests the Stability AI configuration
- Creates the `temp_images/` directory
- Provides helpful setup instructions
- Validates the API key and service connectivity

**Example:**
```bash
python scripts/setup_stability_ai.py sk-1WPMEBzP8fp4yvFhvGf87E39GC23l280GOGFyFCk4fKr5gGx
```

## File Structure

```
backend/
├── scripts/
│   ├── README.md                    # This file
│   └── setup_stability_ai.py        # Stability AI setup utility
├── app/
│   └── services/
│       └── stability_service.py     # Core Stability AI service (runtime)
└── ...
```

## Notes

- **`stability_service.py`** is the core service used during application runtime
- **`setup_stability_ai.py`** is a one-time setup utility for developers
- Both files serve different purposes and should be kept separate 