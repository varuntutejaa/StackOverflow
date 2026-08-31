/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: process.cwd(),
  eslint: { ignoreDuringBuilds: true },
  async rewrites() {
    const api = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    return [{ source: "/proxy/:path*", destination: `${api}/:path*` }];
  },
};
export default nextConfig;
