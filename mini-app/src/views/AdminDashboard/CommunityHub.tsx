import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Users,
  Calendar,
  Gift,
  Heart,
  Star,
  MapPin,
  Clock,
  Plus,
  Check,
  X,
  HelpCircle,
  UserPlus,
  Trophy,
  Sparkles,
  PartyPopper,
  Cake,
  MessageCircle,
  Settings,
  Search,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'
import * as communityAPI from '../../api/community'

Modal.setAppElement('#root')

type TabType = 'events' | 'birthdays' | 'profiles' | 'matching' | 'milestones'
type RSVPStatus = 'going' | 'maybe' | 'not_going'

export default function CommunityHub() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>('events')
  const [events, setEvents] = useState<communityAPI.GroupEvent[]>([])
  const [birthdays, setBirthdays] = useState<communityAPI.BirthdayMember[]>([])
  const [todaysBirthdays, setTodaysBirthdays] = useState<communityAPI.BirthdayMember[]>([])
  const [milestones, setMilestones] = useState<communityAPI.GroupMilestone[]>([])
  const [matches, setMatches] = useState<communityAPI.MemberMatch[]>([])
  const [interestGroups, setInterestGroups] = useState<communityAPI.InterestGroup[]>([])
  const [profile, setProfile] = useState<communityAPI.MemberProfile | null>(null)
  const [stats, setStats] = useState<any>(null)
  
  // Modal states
  const [eventModalOpen, setEventModalOpen] = useState(false)
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const [milestoneModalOpen, setMilestoneModalOpen] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<communityAPI.GroupEvent | null>(null)
  const [rsvpModalOpen, setRsvpModalOpen] = useState(false)
  
  // Form states
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    starts_at: '',
    location: '',
    is_recurring: false
  })
  const [profileForm, setProfileForm] = useState({
    bio: '',
    birthday: '',
    interests: [] as string[],
    social_links: {} as Record<string, string>,
    is_public: true
  })
  const [milestoneForm, setMilestoneForm] = useState({
    title: '',
    description: ''
  })
  const [newInterest, setNewInterest] = useState('')

  useEffect(() => {
    loadData()
  }, [groupId, activeTab])

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)

    try {
      switch (activeTab) {
        case 'events':
          const eventsRes = await communityAPI.getEvents(parseInt(groupId))
          setEvents(eventsRes)
          break
        case 'birthdays':
          const [upcoming, today] = await Promise.all([
            communityAPI.getUpcomingBirthdays(parseInt(groupId), 30),
            communityAPI.getTodaysBirthdays(parseInt(groupId))
          ])
          setBirthdays(upcoming)
          setTodaysBirthdays(today)
          break
        case 'profiles':
          const [profileRes, groupsRes, statsRes] = await Promise.all([
            communityAPI.getMemberProfile(parseInt(groupId)),
            communityAPI.getInterestGroups(parseInt(groupId)),
            communityAPI.getCommunityStats(parseInt(groupId))
          ])
          setProfile(profileRes)
          setInterestGroups(groupsRes)
          setStats(statsRes)
          if (profileRes) {
            setProfileForm({
              bio: profileRes.bio || '',
              birthday: profileRes.birthday || '',
              interests: profileRes.interests || [],
              social_links: profileRes.social_links || {},
              is_public: profileRes.is_public
            })
          }
          break
        case 'matching':
          const matchesRes = await communityAPI.getMemberMatches(parseInt(groupId), 10)
          setMatches(matchesRes)
          break
        case 'milestones':
          const milestonesRes = await communityAPI.getMilestones(parseInt(groupId), 20)
          setMilestones(milestonesRes)
          break
      }
    } catch (error) {
      console.error('Failed to load community data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateEvent = async () => {
    if (!groupId || !eventForm.title || !eventForm.starts_at) return
    try {
      await communityAPI.createEvent(parseInt(groupId), eventForm)
      toast.success('Event created!')
      setEventModalOpen(false)
      setEventForm({ title: '', description: '', starts_at: '', location: '', is_recurring: false })
      loadData()
    } catch (error) {
      toast.error('Failed to create event')
    }
  }

  const handleRSVP = async (status: RSVPStatus) => {
    if (!groupId || !selectedEvent) return
    try {
      await communityAPI.rsvpEvent(parseInt(groupId), selectedEvent.id, status)
      toast.success(`RSVP'd: ${status}`)
      setRsvpModalOpen(false)
      loadData()
    } catch (error) {
      toast.error('Failed to RSVP')
    }
  }

  const handleUpdateProfile = async () => {
    if (!groupId) return
    try {
      await communityAPI.updateMemberProfile(parseInt(groupId), profileForm)
      toast.success('Profile updated!')
      setProfileModalOpen(false)
      loadData()
    } catch (error) {
      toast.error('Failed to update profile')
    }
  }

  const handleCreateMilestone = async () => {
    if (!groupId || !milestoneForm.title) return
    try {
      await communityAPI.createMilestone(parseInt(groupId), milestoneForm)
      toast.success('Milestone created!')
      setMilestoneModalOpen(false)
      setMilestoneForm({ title: '', description: '' })
      loadData()
    } catch (error) {
      toast.error('Failed to create milestone')
    }
  }

  const addInterest = () => {
    if (newInterest && !profileForm.interests.includes(newInterest)) {
      setProfileForm(prev => ({ ...prev, interests: [...prev.interests, newInterest] }))
      setNewInterest('')
    }
  }

  const removeInterest = (interest: string) => {
    setProfileForm(prev => ({ ...prev, interests: prev.interests.filter(i => i !== interest) }))
  }

  const getRSVPStatusIcon = (status?: RSVPStatus) => {
    switch (status) {
      case 'going': return <Check className="w-4 h-4 text-green-400" />
      case 'maybe': return <HelpCircle className="w-4 h-4 text-yellow-400" />
      case 'not_going': return <X className="w-4 h-4 text-red-400" />
      default: return null
    }
  }

  if (loading && !events.length && !profile) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-xl flex items-center justify-center">
            <Users className="w-6 h-6 text-pink-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Community Hub</h1>
            <p className="text-dark-400 mt-1">Events, birthdays, and member connections</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'events', label: 'Events', icon: Calendar },
          { id: 'birthdays', label: 'Birthdays', icon: Cake },
          { id: 'profiles', label: 'Profiles', icon: UserPlus },
          { id: 'matching', label: 'Matching', icon: Heart },
          { id: 'milestones', label: 'Milestones', icon: Trophy },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Events Tab */}
      {activeTab === 'events' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Upcoming Events</h3>
            <button
              onClick={() => setEventModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Event
            </button>
          </div>

          <div className="grid gap-4">
            {events.length === 0 ? (
              <Card>
                <div className="text-center py-12">
                  <Calendar className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No upcoming events</p>
                  <button
                    onClick={() => setEventModalOpen(true)}
                    className="text-primary-400 hover:text-primary-300 mt-2"
                  >
                    Create your first event
                  </button>
                </div>
              </Card>
            ) : (
              events.map(event => (
                <Card key={event.id} className="hover:border-dark-700 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          event.status === 'upcoming' ? 'bg-green-500/20 text-green-400' :
                          event.status === 'ongoing' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-dark-700 text-dark-400'
                        }`}>
                          {event.status}
                        </span>
                        {event.is_recurring && (
                          <span className="px-2 py-0.5 bg-purple-500/20 rounded text-xs text-purple-400">
                            Recurring
                          </span>
                        )}
                      </div>
                      <h4 className="text-lg font-semibold text-white">{event.title}</h4>
                      {event.description && (
                        <p className="text-dark-400 text-sm mt-1">{event.description}</p>
                      )}
                      <div className="flex flex-wrap gap-4 mt-3 text-sm text-dark-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {new Date(event.starts_at).toLocaleString()}
                        </span>
                        {event.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            {event.location}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {event.rsvp_count} going
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col gap-2 ml-4">
                      {event.user_rsvp && (
                        <span className="flex items-center gap-1 px-3 py-1 bg-dark-800 rounded-lg text-sm">
                          {getRSVPStatusIcon(event.user_rsvp)}
                          <span className="capitalize">{event.user_rsvp}</span>
                        </span>
                      )}
                      <button
                        onClick={() => {
                          setSelectedEvent(event)
                          setRsvpModalOpen(true)
                        }}
                        className="px-4 py-2 bg-dark-800 hover:bg-dark-700 rounded-lg text-white text-sm transition-colors"
                      >
                        RSVP
                      </button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Birthdays Tab */}
      {activeTab === 'birthdays' && (
        <div className="space-y-6">
          {/* Today's Birthdays */}
          {todaysBirthdays.length > 0 && (
            <Card className="bg-gradient-to-r from-pink-500/10 via-purple-500/10 to-yellow-500/10 border-pink-500/20">
              <div className="flex items-center gap-2 mb-4">
                <PartyPopper className="w-5 h-5 text-pink-400" />
                <h3 className="font-semibold text-white">Today's Birthdays!</h3>
              </div>
              <div className="flex flex-wrap gap-3">
                {todaysBirthdays.map(member => (
                  <div key={member.user_id} className="flex items-center gap-2 px-4 py-2 bg-dark-900/50 rounded-xl">
                    <Cake className="w-4 h-4 text-pink-400" />
                    <span className="text-white font-medium">{member.first_name}</span>
                    {member.age && <span className="text-dark-400">turns {member.age}!</span>}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Upcoming Birthdays */}
          <Card title="Upcoming Birthdays" icon={Calendar}>
            <div className="space-y-3 mt-4">
              {birthdays.length === 0 ? (
                <p className="text-dark-400 text-center py-8">No upcoming birthdays</p>
              ) : (
                birthdays.map(member => (
                  <div key={member.user_id} className="flex items-center justify-between p-3 bg-dark-800/50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-pink-400 to-purple-500 rounded-full flex items-center justify-center text-sm font-bold text-white">
                        {member.first_name.charAt(0)}
                      </div>
                      <div>
                        <p className="text-white font-medium">{member.first_name}</p>
                        <p className="text-sm text-dark-400">
                          {new Date(member.birthday).toLocaleDateString(undefined, { month: 'long', day: 'numeric' })}
                        </p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-lg text-sm ${
                      member.days_until === 0 ? 'bg-pink-500/20 text-pink-400' :
                      member.days_until <= 7 ? 'bg-purple-500/20 text-purple-400' :
                      'bg-dark-700 text-dark-400'
                    }`}>
                      {member.days_until === 0 ? 'Today!' : `${member.days_until} days`}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Profiles Tab */}
      {activeTab === 'profiles' && (
        <div className="space-y-6">
          {/* Your Profile */}
          <Card className="bg-gradient-to-br from-primary-500/10 to-purple-500/10 border-primary-500/20">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-br from-primary-400 to-purple-500 rounded-2xl flex items-center justify-center text-2xl font-bold text-white">
                  {profile?.first_name?.charAt(0) || '?'}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">{profile?.first_name || 'Your Profile'}</h3>
                  <p className="text-dark-400">{profile?.bio || 'No bio yet'}</p>
                </div>
              </div>
              <button
                onClick={() => setProfileModalOpen(true)}
                className="px-4 py-2 bg-dark-800 hover:bg-dark-700 rounded-lg text-white text-sm transition-colors"
              >
                Edit Profile
              </button>
            </div>

            {profile?.interests && profile.interests.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4">
                {profile.interests.map(interest => (
                  <span key={interest} className="px-3 py-1 bg-dark-800/50 rounded-full text-sm text-primary-400">
                    {interest}
                  </span>
                ))}
              </div>
            )}

            {profile?.birthday && (
              <div className="flex items-center gap-2 mt-4 text-sm text-dark-400">
                <Cake className="w-4 h-4" />
                Born {new Date(profile.birthday).toLocaleDateString()}
              </div>
            )}
          </Card>

          {/* Interest Groups */}
          <Card title="Interest Groups" icon={Heart}>
            <div className="grid grid-cols-2 gap-3 mt-4">
              {interestGroups.map(group => (
                <div
                  key={group.id}
                  className={`p-4 rounded-xl border transition-colors ${
                    group.is_member
                      ? 'bg-primary-500/10 border-primary-500/30'
                      : 'bg-dark-800/50 border-dark-700 hover:border-dark-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl">{group.emoji}</span>
                    {group.is_member && <Check className="w-4 h-4 text-primary-400" />}
                  </div>
                  <h4 className="font-medium text-white">{group.name}</h4>
                  <p className="text-xs text-dark-400 mt-1">{group.member_count} members</p>
                  <button
                    onClick={() => {
                      if (group.is_member) {
                        communityAPI.leaveInterestGroup(parseInt(groupId!), group.id).then(loadData)
                      } else {
                        communityAPI.joinInterestGroup(parseInt(groupId!), group.id).then(loadData)
                      }
                    }}
                    className={`w-full mt-3 py-1.5 rounded-lg text-sm transition-colors ${
                      group.is_member
                        ? 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                        : 'bg-primary-600 text-white hover:bg-primary-700'
                    }`}
                  >
                    {group.is_member ? 'Leave' : 'Join'}
                  </button>
                </div>
              ))}
            </div>
          </Card>

          {stats && (
            <div className="grid grid-cols-3 gap-4">
              <StatCard title="Total Members" value={stats.total_members} icon={Users} />
              <StatCard title="Active Today" value={stats.active_today} icon={Sparkles} />
              <StatCard title="New This Week" value={stats.new_this_week} icon={UserPlus} />
            </div>
          )}
        </div>
      )}

      {/* Matching Tab */}
      {activeTab === 'matching' && (
        <div className="space-y-6">
          <Card title="Member Matches" icon={Heart} description="Connect with members who share your interests">
            <div className="space-y-3 mt-4">
              {matches.length === 0 ? (
                <div className="text-center py-12">
                  <Heart className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No matches found yet</p>
                  <p className="text-sm text-dark-500 mt-1">Complete your profile to find matches</p>
                </div>
              ) : (
                matches.map(match => (
                  <div key={match.user_id} className="flex items-center gap-4 p-4 bg-dark-800/50 rounded-xl">
                    <div className="w-12 h-12 bg-gradient-to-br from-pink-400 to-purple-500 rounded-full flex items-center justify-center text-lg font-bold text-white">
                      {match.first_name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-white">{match.first_name}</h4>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          match.compatibility === 'high' ? 'bg-green-500/20 text-green-400' :
                          match.compatibility === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-dark-700 text-dark-400'
                        }`}>
                          {match.compatibility} match
                        </span>
                      </div>
                      <p className="text-sm text-dark-400">
                        {match.common_interests.length} shared interests
                      </p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {match.common_interests.slice(0, 3).map(interest => (
                          <span key={interest} className="text-xs text-primary-400">#{interest}</span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-bold text-white">{match.match_score}%</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Milestones Tab */}
      {activeTab === 'milestones' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Group Milestones</h3>
            <button
              onClick={() => setMilestoneModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Milestone
            </button>
          </div>

          <div className="space-y-3">
            {milestones.length === 0 ? (
              <Card>
                <div className="text-center py-12">
                  <Trophy className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No milestones recorded</p>
                </div>
              </Card>
            ) : (
              milestones.map(milestone => (
                <Card key={milestone.id} className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Trophy className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-white">{milestone.title}</h4>
                    {milestone.description && (
                      <p className="text-dark-400 text-sm mt-1">{milestone.description}</p>
                    )}
                    <p className="text-dark-500 text-sm mt-2">
                      {new Date(milestone.happened_at).toLocaleDateString()}
                      {milestone.auto_generated && ' • Auto-generated'}
                    </p>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Create Event Modal */}
      <Modal
        isOpen={eventModalOpen}
        onRequestClose={() => setEventModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800 max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold text-white mb-6">Create Event</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Event Title</label>
              <input
                type="text"
                value={eventForm.title}
                onChange={(e) => setEventForm(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter event title"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Description</label>
              <textarea
                value={eventForm.description}
                onChange={(e) => setEventForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="What's happening?"
                rows={3}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Date & Time</label>
              <input
                type="datetime-local"
                value={eventForm.starts_at}
                onChange={(e) => setEventForm(prev => ({ ...prev, starts_at: e.target.value }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Location (optional)</label>
              <input
                type="text"
                value={eventForm.location}
                onChange={(e) => setEventForm(prev => ({ ...prev, location: e.target.value }))}
                placeholder="Where is it happening?"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={eventForm.is_recurring}
                onChange={(e) => setEventForm(prev => ({ ...prev, is_recurring: e.target.checked }))}
                className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
              />
              <span className="text-sm text-dark-300">Recurring event</span>
            </label>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setEventModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateEvent}
              disabled={!eventForm.title || !eventForm.starts_at}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Create Event
            </button>
          </div>
        </div>
      </Modal>

      {/* RSVP Modal */}
      <Modal
        isOpen={rsvpModalOpen}
        onRequestClose={() => setRsvpModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-sm border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-2">{selectedEvent?.title}</h2>
          <p className="text-dark-400 text-sm mb-6">Are you going to this event?</p>
          
          <div className="space-y-2">
            <button
              onClick={() => handleRSVP('going')}
              className="w-full py-3 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 rounded-xl text-green-400 font-medium transition-colors"
            >
              <Check className="w-5 h-5 inline mr-2" />
              Going
            </button>
            <button
              onClick={() => handleRSVP('maybe')}
              className="w-full py-3 bg-yellow-500/20 hover:bg-yellow-500/30 border border-yellow-500/30 rounded-xl text-yellow-400 font-medium transition-colors"
            >
              <HelpCircle className="w-5 h-5 inline mr-2" />
              Maybe
            </button>
            <button
              onClick={() => handleRSVP('not_going')}
              className="w-full py-3 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 rounded-xl text-red-400 font-medium transition-colors"
            >
              <X className="w-5 h-5 inline mr-2" />
              Not Going
            </button>
          </div>
        </div>
      </Modal>

      {/* Profile Modal */}
      <Modal
        isOpen={profileModalOpen}
        onRequestClose={() => setProfileModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800 max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold text-white mb-6">Edit Profile</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Bio</label>
              <textarea
                value={profileForm.bio}
                onChange={(e) => setProfileForm(prev => ({ ...prev, bio: e.target.value }))}
                placeholder="Tell us about yourself"
                rows={3}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Birthday</label>
              <input
                type="date"
                value={profileForm.birthday}
                onChange={(e) => setProfileForm(prev => ({ ...prev, birthday: e.target.value }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Interests</label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newInterest}
                  onChange={(e) => setNewInterest(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addInterest())}
                  placeholder="Add an interest"
                  className="flex-1 px-4 py-2 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
                />
                <button
                  onClick={addInterest}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {profileForm.interests.map(interest => (
                  <span key={interest} className="flex items-center gap-1 px-3 py-1 bg-primary-500/20 rounded-full text-sm text-primary-400">
                    {interest}
                    <button onClick={() => removeInterest(interest)} className="hover:text-primary-300">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={profileForm.is_public}
                onChange={(e) => setProfileForm(prev => ({ ...prev, is_public: e.target.checked }))}
                className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
              />
              <span className="text-sm text-dark-300">Make profile public</span>
            </label>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setProfileModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdateProfile}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors"
            >
              Save Profile
            </button>
          </div>
        </div>
      </Modal>

      {/* Milestone Modal */}
      <Modal
        isOpen={milestoneModalOpen}
        onRequestClose={() => setMilestoneModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">Add Milestone</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Title</label>
              <input
                type="text"
                value={milestoneForm.title}
                onChange={(e) => setMilestoneForm(prev => ({ ...prev, title: e.target.value }))}
                placeholder="e.g., Reached 1000 members!"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Description (optional)</label>
              <textarea
                value={milestoneForm.description}
                onChange={(e) => setMilestoneForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="More details about this milestone"
                rows={3}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setMilestoneModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateMilestone}
              disabled={!milestoneForm.title}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Add Milestone
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
