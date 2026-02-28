import { ReactNode } from 'react'
import { LucideIcon } from 'lucide-react'

interface CardProps {
  title?: string
  description?: string
  icon?: LucideIcon
  children: ReactNode
  className?: string
  onClick?: () => void
}

export default function Card({
  title,
  description,
  icon: Icon,
  children,
  className = '',
  onClick,
}: CardProps) {
  return (
    <div
      className={`
        bg-dark-900 rounded-xl border border-dark-800 p-4
        ${onClick ? 'cursor-pointer hover:border-dark-700 hover:bg-dark-800' : ''}
        transition-all duration-200
        ${className}
      `}
      onClick={onClick}
    >
      {(title || Icon) && (
        <div className="flex items-start gap-3 mb-3">
          {Icon && (
            <div className="p-2 bg-primary-500/10 rounded-lg">
              <Icon className="w-5 h-5 text-primary-500" />
            </div>
          )}
          <div className="flex-1">
            {title && (
              <h3 className="font-semibold text-white">{title}</h3>
            )}
            {description && (
              <p className="text-sm text-dark-400 mt-1">{description}</p>
            )}
          </div>
        </div>
      )}
      {children}
    </div>
  )
}
