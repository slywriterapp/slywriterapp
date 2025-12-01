import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

// Last deploy: 2025-11-30 - v2.9.19
export const metadata: Metadata = {
  title: 'SlyWriter - Premium Typing Assistant',
  description: 'Professional typing automation with AI-powered features',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-black`}>
        {children}
      </body>
    </html>
  )
}