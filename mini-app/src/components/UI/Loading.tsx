import { Loader2 } from 'lucide-react'

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  fullscreen?: boolean
}

const sizeClasses = {
  sm: 'w-5 h-5',
  md: 'w-8 h-8',
  lg: 'w-10 h-10',
}

export default function Loading({ size = 'lg', text = 'Loading Nexus...', fullscreen = true }: LoadingProps) {
  const content = (
    <div className="flex flex-col items-center gap-3 sm:gap-4">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-primary-500`} />
      {text && <p className="text-dark-400 text-sm sm:text-base">{text}</p>}
    </div>
  )

  if (fullscreen) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] sm:min-h-screen">
        {content}
      </div>
    )
  }

  return content
}
