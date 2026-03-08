/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Disable React strict mode to prevent double renders
  reactStrictMode: false,
  env: {
    API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001',
  },
}

module.exports = nextConfig
