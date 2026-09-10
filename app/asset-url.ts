export const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
export const assetUrl = (path: string) => `${basePath}${path}`;
