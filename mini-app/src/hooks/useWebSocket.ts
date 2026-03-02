/**
 * WebSocket Hook - Real-time connection to Nexus backend.
 * 
 * Provides a React hook for connecting to the WebSocket server
 * and receiving real-time events.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

// Event types matching the backend EventType enum
export const EventTypes = {
  // Message events
  MESSAGE_NEW: 'message_new',
  MESSAGE_EDITED: 'message_edited',
  MESSAGE_DELETED: 'message_deleted',
  MESSAGE_RESTORED: 'message_restored',
  
  // Member events
  MEMBER_JOINED: 'member_joined',
  MEMBER_LEFT: 'member_left',
  MEMBER_KICKED: 'member_kicked',
  MEMBER_BANNED: 'member_banned',
  MEMBER_UNBANNED: 'member_unbanned',
  MEMBER_MUTED: 'member_muted',
  MEMBER_UNMUTED: 'member_unmuted',
  MEMBER_WARNED: 'member_warned',
  MEMBER_WARN_REMOVED: 'member_warn_removed',
  MEMBER_PROMOTED: 'member_promoted',
  MEMBER_DEMOTED: 'member_demoted',
  MEMBER_APPROVED: 'member_approved',
  MEMBER_TRUST_CHANGED: 'member_trust_changed',
  MEMBER_XP_CHANGED: 'member_xp_changed',
  MEMBER_LEVEL_UP: 'member_level_up',
  MEMBER_PROFILE_UPDATED: 'member_profile_updated',
  
  // Moderation events
  MOD_ACTION: 'mod_action',
  MOD_ACTION_REVERSED: 'mod_action_reversed',
  FLOOD_DETECTED: 'flood_detected',
  RAID_DETECTED: 'raid_detected',
  WORD_FILTER_TRIGGERED: 'word_filter_triggered',
  LOCK_VIOLATION: 'lock_violation',
  AI_FLAGGED: 'ai_flagged',
  
  // Economy events
  COINS_EARNED: 'coins_earned',
  COINS_SPENT: 'coins_spent',
  COINS_TRANSFERRED: 'coins_transferred',
  COINS_ADMIN_GRANTED: 'coins_admin_granted',
  COINS_ADMIN_REVOKED: 'coins_admin_revoked',
  BONUS_EVENT_STARTED: 'bonus_event_started',
  BONUS_EVENT_ENDED: 'bonus_event_ended',
  
  // Module events
  MODULE_ENABLED: 'module_enabled',
  MODULE_DISABLED: 'module_disabled',
  MODULE_CONFIG_CHANGED: 'module_config_changed',
  
  // Lock events
  LOCK_ENABLED: 'lock_enabled',
  LOCK_DISABLED: 'lock_disabled',
  
  // System events
  SYSTEM_ERROR: 'system_error',
  MODULE_HEALTH_CHECK_FAILED: 'module_health_check_failed',
  MODULE_HEALTH_CHECK_PASSED: 'module_health_check_passed',
} as const;

export type EventType = typeof EventTypes[keyof typeof EventTypes];

export interface NexusEvent {
  event_type: EventType;
  group_id: number;
  timestamp: string;
  event_id: string;
  
  // Actor
  actor_id?: number;
  actor_telegram_id?: number;
  actor_name?: string;
  
  // Target
  target_id?: number;
  target_telegram_id?: number;
  target_name?: string;
  
  // Details
  data?: Record<string, any>;
  message_id?: number;
  channel_id?: number;
  
  // Moderation
  reason?: string;
  duration_seconds?: number;
  silent?: boolean;
  
  // AI
  ai_inferred?: boolean;
  ai_confidence?: number;
}

export interface WSMessage {
  type: 'event' | 'command' | 'ping' | 'pong' | 'error' | 'connected' | 'subscribed' | 'command_result';
  data?: NexusEvent | Record<string, any>;
  timestamp: string;
}

export interface UseWebSocketOptions {
  groupId: number;
  userId?: number;
  telegramId?: number;
  username?: string;
  token?: string;
  autoConnect?: boolean;
  onEvent?: (event: NexusEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: string) => void;
  subscribedEvents?: EventType[];
}

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastEvent: NexusEvent | null;
  eventHistory: NexusEvent[];
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    groupId,
    userId,
    telegramId,
    username,
    token,
    autoConnect = true,
    onEvent,
    onConnect,
    onDisconnect,
    onError,
    subscribedEvents,
  } = options;
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    connecting: false,
    error: null,
    lastEvent: null,
    eventHistory: [],
  });
  
  // Build WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    let url = `${protocol}//${host}/ws/${groupId}`;
    
    const params = new URLSearchParams();
    if (userId) params.set('user_id', userId.toString());
    if (telegramId) params.set('telegram_id', telegramId.toString());
    if (username) params.set('username', username);
    if (token) params.set('token', token);
    
    const queryString = params.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
    
    return url;
  }, [groupId, userId, telegramId, username, token]);
  
  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    setState(prev => ({ ...prev, connecting: true, error: null }));
    
    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);
      wsRef.current = ws;
      
      ws.onopen = () => {
        setState(prev => ({ ...prev, connected: true, connecting: false, error: null }));
        
        // Subscribe to specific events if provided
        if (subscribedEvents && subscribedEvents.length > 0) {
          ws.send(JSON.stringify({
            type: 'subscribe',
            data: { events: subscribedEvents }
          }));
        }
        
        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Ping every 30 seconds
        
        onConnect?.();
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          
          if (message.type === 'event' && message.data) {
            const nexusEvent = message.data as NexusEvent;
            
            setState(prev => ({
              ...prev,
              lastEvent: nexusEvent,
              eventHistory: [nexusEvent, ...prev.eventHistory].slice(0, 100), // Keep last 100 events
            }));
            
            onEvent?.(nexusEvent);
          } else if (message.type === 'error') {
            const errorMsg = (message.data as any)?.message || 'Unknown error';
            setState(prev => ({ ...prev, error: errorMsg }));
            onError?.(errorMsg);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };
      
      ws.onclose = (event) => {
        setState(prev => ({ ...prev, connected: false, connecting: false }));
        
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        
        onDisconnect?.();
        
        // Auto-reconnect after 5 seconds
        if (event.code !== 1000) { // Don't reconnect on normal close
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 5000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ ...prev, error: 'WebSocket connection error', connecting: false }));
        onError?.('WebSocket connection error');
      };
      
    } catch (err: any) {
      setState(prev => ({ ...prev, error: err.message, connecting: false }));
      onError?.(err.message);
    }
  }, [getWebSocketUrl, subscribedEvents, onConnect, onDisconnect, onError, onEvent]);
  
  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000); // Normal close
      wsRef.current = null;
    }
    
    setState(prev => ({ ...prev, connected: false }));
  }, []);
  
  // Send command through WebSocket
  const sendCommand = useCallback((action: string, params?: Record<string, any>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        data: { action, params }
      }));
      return true;
    }
    return false;
  }, []);
  
  // Subscribe to specific events
  const subscribe = useCallback((events: EventType[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        data: { events }
      }));
      return true;
    }
    return false;
  }, []);
  
  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);
  
  return {
    ...state,
    connect,
    disconnect,
    sendCommand,
    subscribe,
  };
}

export default useWebSocket;
