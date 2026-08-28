import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true, // مطلوبة عند استخدام static export في Next.js
  },
};

export default nextConfig;