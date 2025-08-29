import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

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
    <html lang="en" className="dark">
      <body className={`${inter.className} overflow-hidden`}>
        <div className="fixed inset-0 purple-blue-gradient" />
        <div className="relative z-10 h-screen">
          {children}
        </div>
      </body>
    </html>
  )
}