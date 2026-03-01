import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Shield, AlertTriangle, UserX, ShieldCheck } from 'lucide-react'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Badge from '../../components/UI/Badge'
import Toggle from '../../components/UI/Toggle'

const mockThreats = [
  { id: 1, type: 'Spam', user: '@spammer123', action: 'Banned', time: '2m ago' },
  { id: 2, type: 'Raid attempt', user: '5 new accounts', action: 'Blocked', time: '1h ago' },
  { id: 3, type: 'Scam link', user: '@user456', action: 'Deleted', time: '3h ago' },
]

export default function SecurityCenter() {
  const [casEnabled, setCasEnabled] = useState(true)
  const [antiRaid, setAntiRaid] = useState(true)
  const [captcha, setCaptcha] = useState(false)
  const [linkProtection, setLinkProtection] = useState(true)

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Security Center</h1>
        <p className="text-dark-400 mt-1">
          Protect your group from threats and spam
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard
          title="Threats Blocked"
          value="24"
          icon={Shield}
        />
        <StatCard
          title="Users Banned"
          value="8"
          icon={UserX}
        />
      </div>

      {/* Security Features */}
      <Card title="Protection Features" icon={ShieldCheck} className="mb-6">
        <div className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">CAS Protection</p>
              <p className="text-dark-400 text-xs">Block known spammers via Combot Anti-Spam</p>
            </div>
            <Toggle checked={casEnabled} onChange={setCasEnabled} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">Anti-Raid</p>
              <p className="text-dark-400 text-xs">Detect and stop coordinated raid attacks</p>
            </div>
            <Toggle checked={antiRaid} onChange={setAntiRaid} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">CAPTCHA on Join</p>
              <p className="text-dark-400 text-xs">Verify new members are human</p>
            </div>
            <Toggle checked={captcha} onChange={setCaptcha} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">Link Protection</p>
              <p className="text-dark-400 text-xs">Remove malicious and phishing links</p>
            </div>
            <Toggle checked={linkProtection} onChange={setLinkProtection} />
          </div>
        </div>
      </Card>

      {/* Threat Log */}
      <Card title="Recent Threats" icon={AlertTriangle}>
        <div className="space-y-3 mt-4">
          {mockThreats.map((threat) => (
            <div key={threat.id} className="flex items-center gap-3 bg-dark-800 rounded-lg p-3">
              <div className="w-8 h-8 bg-red-500/10 rounded-full flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-4 h-4 text-red-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium">{threat.type}</p>
                <p className="text-dark-400 text-xs truncate">{threat.user}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <Badge variant="error">{threat.action}</Badge>
                <p className="text-dark-500 text-xs mt-1">{threat.time}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-dark-700">
          <p className="text-dark-400 text-sm text-center">
            Configure security with <code className="text-primary-400">/antiflood</code> and <code className="text-primary-400">/antiraid</code>
          </p>
        </div>
      </Card>
    </div>
  )
}
