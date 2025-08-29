# SlyWriter UI - Full Setup

## After creating the Next.js app, run these commands:

```bash
cd slywriter-ui

# Install all dependencies we need
npm install @radix-ui/react-dialog @radix-ui/react-slider @radix-ui/react-switch @radix-ui/react-tabs @radix-ui/react-toast @radix-ui/react-dropdown-menu @radix-ui/react-progress
npm install framer-motion axios clsx tailwind-merge class-variance-authority
npm install lucide-react react-hot-toast recharts
npm install @tanstack/react-query

# Install dev dependencies
npm install -D @types/node
```

## File Structure I'll Create:
```
slywriter-ui/
├── app/
│   ├── layout.tsx       # Main layout with gradient
│   ├── page.tsx         # Main app
│   ├── globals.css      # Tailwind + animations
│   └── api.ts          # API client
├── components/
│   ├── Sidebar.tsx      # Navigation
│   ├── TypingTab.tsx    # Main typing interface
│   ├── StatusBar.tsx    # Real-time status
│   ├── Controls.tsx     # Start/Stop/Pause
│   └── StatsCards.tsx   # WPM, progress, etc.
└── lib/
    └── utils.ts         # Helper functions
```

## The Purple to Deep Blue gradient you want:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #6B8DD6 50%, #8E37D7 75%, #206ECF 100%);
```

## Tell me when Next.js is done installing!