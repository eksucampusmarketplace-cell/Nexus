import { create } from 'zustand'
import { Group } from '../api/groups'

interface GroupState {
  groups: Group[]
  currentGroup: Group | null
  isLoading: boolean
  setGroups: (groups: Group[]) => void
  setCurrentGroup: (group: Group | null) => void
  addGroup: (group: Group) => void
  updateGroup: (groupId: number, updates: Partial<Group>) => void
  setLoading: (loading: boolean) => void
}

export const useGroupStore = create<GroupState>((set) => ({
  groups: [],
  currentGroup: null,
  isLoading: false,
  setGroups: (groups) => set({ groups }),
  setCurrentGroup: (group) => set({ currentGroup: group }),
  addGroup: (group) => set((state) => ({ groups: [...state.groups, group] })),
  updateGroup: (groupId, updates) =>
    set((state) => ({
      groups: state.groups.map((g) =>
        g.id === groupId ? { ...g, ...updates } : g
      ),
      currentGroup:
        state.currentGroup?.id === groupId
          ? { ...state.currentGroup, ...updates }
          : state.currentGroup,
    })),
  setLoading: (loading) => set({ isLoading: loading }),
}))
