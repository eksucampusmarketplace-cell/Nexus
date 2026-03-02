import { ReactNode } from 'react'

interface MainLayoutProps {
  children: ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-dark-950 safe-area-top safe-area-bottom safe-area-x">
      {/* Mobile: full width with small padding */}
      {/* Tablet: max width with medium padding */}
      {/* Desktop: constrained width with larger padding */}
      <div className="
        w-full mx-auto
        px-3 sm:px-4 lg:px-6 xl:px-8
        max-w-full
        sm:max-w-3xl
        lg:max-w-5xl
        xl:max-w-6xl
        2xl:max-w-7xl
      ">
        <main className="py-3 sm:py-4 lg:py-6 pb-20 sm:pb-6">
          {children}
        </main>
      </div>
    </div>
  )
}
