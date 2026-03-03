interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  size?: 'sm' | 'md'
  className?: string
}

const variants = {
  default: 'bg-dark-700 text-dark-200',
  success: 'bg-green-500/20 text-green-500',
  warning: 'bg-yellow-500/20 text-yellow-500',
  error: 'bg-red-500/20 text-red-500',
  info: 'bg-primary-500/20 text-primary-500',
}

const sizes = {
  sm: 'px-1.5 sm:px-2 py-0.5 text-xxs sm:text-xs',
  md: 'px-2 sm:px-2.5 py-0.5 text-xs sm:text-sm',
}

export default function Badge({ children, variant = 'default', size = 'sm', className = '' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center font-medium rounded-full whitespace-nowrap ${variants[variant]} ${sizes[size]} ${className}`}>
      {children}
    </span>
  )
}
