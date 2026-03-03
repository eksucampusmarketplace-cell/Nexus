import api from './client'

export interface PublicConfig {
  bot_username: string
  environment: string
}

const defaultConfig: PublicConfig = {
  bot_username: 'nexusbot',
  environment: 'production',
}

let cachedConfig: PublicConfig | null = null
let configPromise: Promise<PublicConfig> | null = null

export const getPublicConfig = async (): Promise<PublicConfig> => {
  // Return cached config if available
  if (cachedConfig) {
    return cachedConfig
  }
  
  // Return existing promise if a request is already in flight
  if (configPromise) {
    return configPromise
  }
  
  // Make the request
  configPromise = api.get('/config')
    .then(response => {
      cachedConfig = response.data as PublicConfig
      return cachedConfig
    })
    .catch(error => {
      console.error('Failed to load public config:', error)
      // Return default config on error
      return defaultConfig
    })
    .finally(() => {
      configPromise = null
    })
  
  return configPromise
}

export const getBotUsername = async (): Promise<string> => {
  const config = await getPublicConfig()
  return config.bot_username
}

export const getAddToGroupUrl = async (): Promise<string> => {
  const botUsername = await getBotUsername()
  return `https://t.me/${botUsername}?startgroup=true`
}
