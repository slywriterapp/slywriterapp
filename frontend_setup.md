# Frontend Setup Instructions

## Prerequisites
You need Node.js installed. If you don't have it:
- Download from: https://nodejs.org/ (get LTS version)
- Install it with default settings

## Setup Commands

Open a NEW terminal/command prompt and run:

```bash
# 1. Navigate to project
cd "C:\Typing Project"

# 2. Create Next.js app with TypeScript and Tailwind
npx create-next-app@latest slywriter-ui --typescript --tailwind --app --no-src-dir --import-alias "@/*"

# When prompted, select:
# ✔ Would you like to use ESLint? → Yes
# ✔ Would you like to use `src/` directory? → No
# ✔ Would you like to use App Router? → Yes
# ✔ Would you like to customize the default import alias? → No

# 3. Navigate to the frontend
cd slywriter-ui

# 4. Install additional dependencies
npm install @radix-ui/react-dialog @radix-ui/react-slider @radix-ui/react-switch @radix-ui/react-tabs
npm install framer-motion axios react-hot-toast
npm install lucide-react class-variance-authority clsx tailwind-merge

# 5. Install shadcn/ui CLI
npx shadcn-ui@latest init

# When prompted:
# ✔ Would you like to use TypeScript? → Yes
# ✔ Which style would you like to use? → Default
# ✔ Which color would you like to use as base color? → Slate
# ✔ Where is your global CSS file? → app/globals.css
# ✔ Would you like to use CSS variables for colors? → Yes
# ✔ Where is your tailwind.config.js located? → tailwind.config.js
# ✔ Configure the import alias for components? → @/components
# ✔ Configure the import alias for utils? → @/lib/utils

# 6. Add shadcn components we'll use
npx shadcn-ui@latest add button card tabs textarea switch slider dialog toast
```

## Next Steps
After running these commands, tell me when you're done and I'll create the actual React components!