# Electron Typing Bridge Architecture

## How It Works (Like Discord/Slack)

### 1. Server Processes Everything
```python
# Server (Python/FastAPI with WebSockets)
@app.websocket("/typing")
async def typing_endpoint(websocket: WebSocket):
    text = await websocket.receive_text()

    # Process text (humanization, AI, etc)
    processed = humanize_text(text)

    # Send typing commands to client
    for char in processed:
        delay = calculate_delay(char)
        await websocket.send_json({
            "action": "type",
            "char": char,
            "delay": delay
        })
```

### 2. Electron Just Types
```javascript
// Electron preload.js - Typing Bridge
const robot = require('robotjs'); // Or node-key-sender

window.typingBridge = {
  connect: () => {
    const ws = new WebSocket('wss://api.slywriter.com/typing');

    ws.onmessage = (event) => {
      const cmd = JSON.parse(event.data);

      if (cmd.action === 'type') {
        setTimeout(() => {
          robot.typeString(cmd.char);
          ws.send(JSON.stringify({status: 'typed', char: cmd.char}));
        }, cmd.delay);
      }
    };
  }
};
```

### 3. Benefits

**Server Side:**
- All heavy processing
- AI text generation
- Usage tracking
- Plan enforcement
- Text humanization algorithms

**Client Side (Electron):**
- Only keyboard simulation
- 50MB instead of 900MB
- No Python needed
- No admin rights needed (robotjs doesn't require admin)
- Instant updates (server-side changes)

### 4. Libraries for Electron Typing

**Option A: robotjs (Recommended)**
```bash
npm install robotjs
```
- Cross-platform
- No admin needed
- Used by Discord, VS Code

**Option B: node-key-sender**
```bash
npm install node-key-sender
```
- Windows-focused
- Very lightweight

**Option C: nut.js**
```bash
npm install @nut-tree/nut-js
```
- Modern, TypeScript
- Good for complex automation

### 5. Implementation Steps

1. **Server WebSocket endpoint** - Processes text, sends commands
2. **Electron typing bridge** - Receives commands, types locally
3. **Remove Python dependency** - All logic on server
4. **Small installer** - Just Electron + typing library (50-80MB)

This is EXACTLY how Discord handles Push-to-Talk, Slack handles notifications, and Spotify controls media keys - server sends commands, thin client executes locally!