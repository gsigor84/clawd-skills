# Tandem Browser Control

Tandem is a local AI-aware browser running at http://127.0.0.1:8765.
Auth token is at ~/.tandem/api-token — read it fresh each time.

## Key endpoints (always use Bearer token header):

GET → current tab URL, title, loading state, viewport
GET /tabs/list → all open tabs with id, url, title
POST /tabs/open → open new tab — body: {"url":"https://..."}
POST /tabs/activate → switch to tab — body: {"tabId":"tab-X"}
POST /tabs/close → close tab — body: {"tabId":"tab-X"}
POST /navigate → navigate current tab — body: {"url":"https://..."}
GET /snapshot → get DOM snapshot of current page
GET /screenshot → take screenshot — returns base64 image
POST /click → click element — body: {"selector":"css selector"}
POST /type → type text — body: {"selector":"...","text":"..."}

## How to use:

- Always read the token fresh from ~/.tandem/api-token using the read tool
- Use exec + curl for all Tandem API calls
- Prefer /snapshot over web_fetch when the user is already on a page in Tandem
- Use /screenshot + image tool to visually verify page state
