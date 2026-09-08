import type { Metadata } from 'next';
import { Cormorant_Garamond, Manrope } from 'next/font/google';
import './globals.css';

const geistSans = Manrope({
  variable: '--font-body',
  subsets: ['latin','latin-ext'],
});

const geistMono = Cormorant_Garamond({
  variable: '--font-display',
  weight:['400','500','600'],
  style:['normal','italic'],
  subsets: ['latin','latin-ext'],
});

export const metadata: Metadata = {
  title: 'KurzusKáosz — Kifogjuk az okokat',
  description: 'Kapás van. Kurzus még nincs. Görgethető 3D horgásztörténet, amely a víz felszínére hozza a kurzusfelvétel húsz okát. Ishikawa-diagram, egy kicsit másképp.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="hu">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
