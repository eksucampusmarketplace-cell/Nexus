import api from './client'

export interface GroupEvent {
  id: number
  title: string
  description?: string
  starts_at: string
  ends_at?: string
  location?: string
  created_by: number
  is_recurring: boolean
  status: 'upcoming' | 'ongoing' | 'ended' | 'cancelled'
  rsvp_count: number
  user_rsvp?: 'going' | 'maybe' | 'not_going'
}

export interface EventRSVP {
  id: number
  event_id: number
  user_id: number
  status: 'going' | 'maybe' | 'not_going'
  rsvp_at: string
  user: {
    id: number
    username: string | null
    first_name: string
  }
}

export interface MemberProfile {
  user_id: number
  username: string | null
  first_name: string
  bio?: string
  birthday?: string
  social_links?: Record<string, string>
  profile_theme: string
  interests?: string[]
  is_public: boolean
}

export interface InterestGroup {
  id: number
  name: string
  description: string
  emoji: string
  member_count: number
  is_member: boolean
  created_at: string
}

export interface BirthdayMember {
  user_id: number
  username: string | null
  first_name: string
  birthday: string
  age?: number
  days_until: number
}

export interface GroupMilestone {
  id: number
  title: string
  description?: string
  happened_at: string
  auto_generated: boolean
}

export interface MemberMatch {
  user_id: number
  username: string | null
  first_name: string
  match_score: number
  common_interests: string[]
  compatibility: 'high' | 'medium' | 'low'
}

export const getEvents = async (groupId: number, status?: string): Promise<GroupEvent[]> => {
  const response = await api.get(`/groups/${groupId}/community/events`, {
    params: { status }
  })
  return response.data
}

export const createEvent = async (groupId: number, data: Partial<GroupEvent>) => {
  const response = await api.post(`/groups/${groupId}/community/events`, data)
  return response.data
}

export const updateEvent = async (groupId: number, eventId: number, data: Partial<GroupEvent>) => {
  const response = await api.patch(`/groups/${groupId}/community/events/${eventId}`, data)
  return response.data
}

export const deleteEvent = async (groupId: number, eventId: number) => {
  const response = await api.delete(`/groups/${groupId}/community/events/${eventId}`)
  return response.data
}

export const rsvpEvent = async (groupId: number, eventId: number, status: 'going' | 'maybe' | 'not_going') => {
  const response = await api.post(`/groups/${groupId}/community/events/${eventId}/rsvp`, { status })
  return response.data
}

export const getEventRSVPs = async (groupId: number, eventId: number): Promise<EventRSVP[]> => {
  const response = await api.get(`/groups/${groupId}/community/events/${eventId}/rsvps`)
  return response.data
}

export const getMemberProfile = async (groupId: number, userId?: number): Promise<MemberProfile> => {
  const url = userId
    ? `/groups/${groupId}/community/profiles/${userId}`
    : `/groups/${groupId}/community/profiles/me`
  const response = await api.get(url)
  return response.data
}

export const updateMemberProfile = async (groupId: number, data: Partial<MemberProfile>) => {
  const response = await api.patch(`/groups/${groupId}/community/profiles/me`, data)
  return response.data
}

export const getInterestGroups = async (groupId: number): Promise<InterestGroup[]> => {
  const response = await api.get(`/groups/${groupId}/community/interest-groups`)
  return response.data
}

export const joinInterestGroup = async (groupId: number, groupId2: number) => {
  const response = await api.post(`/groups/${groupId}/community/interest-groups/${groupId2}/join`)
  return response.data
}

export const leaveInterestGroup = async (groupId: number, groupId2: number) => {
  const response = await api.post(`/groups/${groupId}/community/interest-groups/${groupId2}/leave`)
  return response.data
}

export const getUpcomingBirthdays = async (groupId: number, days = 30): Promise<BirthdayMember[]> => {
  const response = await api.get(`/groups/${groupId}/community/birthdays/upcoming`, {
    params: { days }
  })
  return response.data
}

export const getTodaysBirthdays = async (groupId: number): Promise<BirthdayMember[]> => {
  const response = await api.get(`/groups/${groupId}/community/birthdays/today`)
  return response.data
}

export const getMilestones = async (groupId: number, limit = 20): Promise<GroupMilestone[]> => {
  const response = await api.get(`/groups/${groupId}/community/milestones`, {
    params: { limit }
  })
  return response.data
}

export const createMilestone = async (groupId: number, data: Partial<GroupMilestone>) => {
  const response = await api.post(`/groups/${groupId}/community/milestones`, data)
  return response.data
}

export const getMemberMatches = async (groupId: number, limit = 10): Promise<MemberMatch[]> => {
  const response = await api.get(`/groups/${groupId}/community/matches`, {
    params: { limit }
  })
  return response.data
}

export const getCommunityStats = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/community/stats`)
  return response.data
}
