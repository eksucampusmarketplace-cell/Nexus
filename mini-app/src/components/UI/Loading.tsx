import { Loader2 } from 'lucide-react'

export default function Loading() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-primary-500" />
        <p className="text-dark-400">Loading Nexus...</p>
      </div>
    </div>
  )
}
