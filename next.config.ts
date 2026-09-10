import type { NextConfig } from 'next';

const pages = process.env.GITHUB_PAGES_BUILD === '1';
const nextConfig: NextConfig = pages ? {
  output: 'export',
  // Vinext beta.5 prerenders paths without basePath. All page navigation uses
  // explicit anchors; assetPrefix and assetUrl handle the Pages mount point.
  assetPrefix: '/kurzuskaosz-horgaszat',
  trailingSlash: false,
  images: {unoptimized: true},
} : {};

export default nextConfig;
