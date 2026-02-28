import api from './client'

export interface PollOption {
  id: number
  text: string
  voter_count: number
}

export interface Poll {
  id: number
  group_id: number
  question: string
  options: string[]
  is_anonymous: boolean
  allows_multiple: boolean
  is_closed: boolean
  message_id?: number
  created_by: number
  created_at: string
  total_votes: number
}

export interface PollWithResults extends Poll {
  options_with_counts: PollOption[]
}

export interface PollStats {
  total_polls: number
  active_polls: number
  closed_polls: number
  recent_polls: {
    id: number
    question: string
    is_closed: boolean
    created_at: string
    total_votes: number
  }[]
}

export const getPolls = async (groupId: number, page = 1, pageSize = 20, includeClosed = false) => {
  const response = await api.get(`/groups/${groupId}/polls`, {
    params: { page, page_size: pageSize, include_closed: includeClosed },
  })
  return response.data
}

export const getPoll = async (groupId: number, pollId: number): Promise<PollWithResults> => {
  const response = await api.get(`/groups/${groupId}/polls/${pollId}`)
  return response.data
}

export const createPoll = async (
  groupId: number,
  data: {
    question: string
    options: string[]
    is_anonymous?: boolean
    allows_multiple?: boolean
    poll_type?: 'regular' | 'quiz' | 'straw'
    correct_option_id?: number
  }
) => {
  const response = await api.post(`/groups/${groupId}/polls`, data)
  return response.data
}

export const closePoll = async (groupId: number, pollId: number) => {
  const response = await api.post(`/groups/${groupId}/polls/${pollId}/close`)
  return response.data
}

export const votePoll = async (groupId: number, pollId: number, optionId: number) => {
  const response = await api.post(`/groups/${groupId}/polls/${pollId}/vote`, null, {
    params: { option_id: optionId },
  })
  return response.data
}

export const deletePoll = async (groupId: number, pollId: number) => {
  const response = await api.delete(`/groups/${groupId}/polls/${pollId}`)
  return response.data
}

export const getPollStats = async (groupId: number): Promise<PollStats> => {
  const response = await api.get(`/groups/${groupId}/polls/stats/summary`)
  return response.data
}
