/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin-allow-popups', // Allow popups for OAuth
          },
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'unsafe-none', // Allow embedding from Google
          },
        ],
      },
    ]
  },
  // Allow images from Google
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'lh3.googleusercontent.com',
        pathname: '/**',
      },
    ],
  },
}

export default nextConfig