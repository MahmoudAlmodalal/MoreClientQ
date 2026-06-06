import React from 'react';
import Nav from '../../components/landing/Nav';
import Footer from '../../components/landing/Footer';

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen flex flex-col bg-[#030712] text-[#F9FAFB] selection:bg-[#6366F1] selection:text-white overflow-x-hidden">
      <Nav />

      {/* Main Content Area */}
      <main className="flex-1 w-full">
        {children}
      </main>

      <Footer />
    </div>
  );
}
