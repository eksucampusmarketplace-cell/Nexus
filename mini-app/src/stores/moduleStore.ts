import { create } from 'zustand'
import { Module } from '../api/modules'

interface ModuleState {
  modules: Module[]
  groupModules: Record<number, Module[]>
  isLoading: boolean
  setModules: (modules: Module[]) => void
  setGroupModules: (groupId: number, modules: Module[]) => void
  updateModuleStatus: (groupId: number, moduleName: string, isEnabled: boolean) => void
  setLoading: (loading: boolean) => void
}

export const useModuleStore = create<ModuleState>((set) => ({
  modules: [],
  groupModules: {},
  isLoading: false,
  setModules: (modules) => set({ modules }),
  setGroupModules: (groupId, modules) =>
    set((state) => ({
      groupModules: { ...state.groupModules, [groupId]: modules },
    })),
  updateModuleStatus: (groupId, moduleName, isEnabled) =>
    set((state) => ({
      groupModules: {
        ...state.groupModules,
        [groupId]: state.groupModules[groupId]?.map((m) =>
          m.name === moduleName ? { ...m, is_enabled: isEnabled } : m
        ) || [],
      },
    })),
  setLoading: (loading) => set({ isLoading: loading }),
}))
