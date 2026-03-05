import api from './client'
import { debugLog, LogCategory, LogLevel, logHashComputation, logAuthState } from '../utils/debug'

export { default as api } from './client'

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: number
  telegram_id: number
  username: string | null
  first_name: string
  last_name: string | null
  language_code: string
  is_premium: boolean
  is_owner: boolean
  is_support: boolean
  is_staff: boolean
}

/**
 * Parse init data for debugging purposes
 */
function parseInitDataForDebug(initData: string): Record<string, string> {
  const params: Record<string, string> = {}
  for (const pair of initData.split('&')) {
    if (pair.includes('=')) {
      const [key, value] = pair.split('=', 2)
      params[key] = decodeURIComponent(value)
    }
  }
  return params
}

/**
 * Compute hash locally for debugging
 * Note: This won't match Telegram's hash without the bot token, 
 * but helps debug the data structure
 */
function computeDebugHash(initData: string): { dataCheckString: string; hash: string } | null {
  try {
    const params: Record<string, string> = {}
    for (const pair of initData.split('&')) {
      if (pair.includes('=')) {
        const [key, value] = pair.split('=', 2)
        params[key] = value
      }
    }
    
    const hash = params['hash']
    delete params['hash']
    delete params['signature']
    
    const dataCheckString = Object.keys(params)
      .sort()
      .map(k => `${k}=${params[k]}`)
      .join('\n')
    
    return { dataCheckString, hash: hash || '' }
  } catch (e) {
    return null
  }
}

// Backend handles bot token lookup based on user's group memberships (database-driven)
// No localStorage needed!
export const telegramAuth = async (initData: string): Promise<AuthResponse & { user: User }> => {
  debugLog(LogCategory.AUTH, '=== TELEGRAM AUTH START ===', null);
  logAuthState('api_call_start');
  
  // Log init data details
  debugLog(LogCategory.AUTH, 'initData length:', initData.length);
  debugLog(LogCategory.AUTH, 'initData (first 200 chars):', initData.substring(0, 200));
  
  // Parse and log init data parameters
  const parsedParams = parseInitDataForDebug(initData);
  debugLog(LogCategory.AUTH, 'Parsed init data params:', {
    hasUser: !!parsedParams.user,
    hasHash: !!parsedParams.hash,
    hashLength: parsedParams.hash?.length,
    authDate: parsedParams.auth_date,
    queryId: parsedParams.query_id ? `${parsedParams.query_id.substring(0, 20)}...` : null,
  });
  
  // Compute debug hash info
  const debugHashInfo = computeDebugHash(initData);
  if (debugHashInfo) {
    debugLog(LogCategory.HASH, 'Data check string (first 200 chars):', debugHashInfo.dataCheckString.substring(0, 200));
    debugLog(LogCategory.HASH, 'Received hash:', `${debugHashInfo.hash.substring(0, 20)}...`);
  }
  
  try {
    debugLog(LogCategory.AUTH, 'Sending auth request to /auth/token', null);
    const startTime = Date.now();
    
    const response = await api.post('/auth/token', { init_data: initData })
    
    const duration = Date.now() - startTime;
    debugLog(LogCategory.AUTH, `Auth request completed in ${duration}ms`, null);
    debugLog(LogCategory.AUTH, 'Auth response received:', {
      hasAccessToken: !!response.data.access_token,
      tokenType: response.data.token_type,
      expiresIn: response.data.expires_in,
      hasUser: !!response.data.user,
      userId: response.data.user?.id,
      userTelegramId: response.data.user?.telegram_id,
      username: response.data.user?.username,
    });
    
    logAuthState('api_call_success');
    debugLog(LogCategory.AUTH, '=== TELEGRAM AUTH SUCCESS ===', null);
    
    return response.data
  } catch (error: any) {
    debugLog(LogCategory.AUTH, 'Auth request failed:', error.message, LogLevel.ERROR);
    debugLog(LogCategory.AUTH, 'Error response:', error.response?.data, LogLevel.ERROR);
    debugLog(LogCategory.AUTH, 'Error status:', error.response?.status, LogLevel.ERROR);
    
    logAuthState('api_call_failed', { 
      status: error.response?.status, 
      detail: error.response?.data?.detail 
    });
    
    debugLog(LogCategory.AUTH, '=== TELEGRAM AUTH FAILED ===', null, LogLevel.ERROR);
    throw error
  }
}

export const getMe = async (): Promise<User> => {
  const response = await api.get('/auth/me')
  return response.data
}

export const getPermissions = async (groupId: number) => {
  const response = await api.get(`/auth/permissions/${groupId}`)
  return response.data
}
