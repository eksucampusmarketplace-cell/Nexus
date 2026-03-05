/**
 * WebSocket Hook - Real-time connection to Nexus backend.
 *
 * Provides a React hook for connecting to the WebSocket server
 * and receiving real-time events.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

// Enhanced debug system
import {
  enhancedDebug,
  telegramDebug,
  ErrorAnalyzer,
  ErrorCode,
  LogCategory,
  LogLevel,
} from '../utils/enhancedDebug';

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

    // Enhanced debug logging
    enhancedDebug.debug('WebSocket URL built', LogCategory.WEBSOCKET, {
      url: url.replace(token || '', token ? '***token***' : ''),
      protocol,
      host,
      groupId,
      hasUserId: !!userId,
      hasTelegramId: !!telegramId,
      hasUsername: !!username,
      hasToken: !!token,
    });

    // Backward compatibility
    enhancedDebug.debug('WebSocket URL built', LogCategory.WEBSOCKET, {
      url: url.replace(token || '', token ? '***token***' : ''),
      protocol,
      host,
      groupId,
    });

    return url;
  }, [groupId, userId, telegramId, username, token]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    enhancedDebug.info('=== WebSocket connect() called ===', LogCategory.WEBSOCKET);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      enhancedDebug.debug('WebSocket already connected, skipping', LogCategory.WEBSOCKET);
      return;
    }

    setState(prev => ({ ...prev, connecting: true, error: null }));
    telegramDebug.logWebSocketEvent('connecting');

    try {
      const url = getWebSocketUrl();
      enhancedDebug.info('Creating new WebSocket connection...', LogCategory.WEBSOCKET, { url });

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        enhancedDebug.success('WebSocket connected successfully', LogCategory.WEBSOCKET);
        setState(prev => ({ ...prev, connected: true, connecting: false, error: null }));
        telegramDebug.logWebSocketEvent('connected');

        // Subscribe to specific events if provided
        if (subscribedEvents && subscribedEvents.length > 0) {
          enhancedDebug.debug('Subscribing to events', LogCategory.WEBSOCKET, { events: subscribedEvents });
          ws.send(JSON.stringify({
            type: 'subscribe',
            data: { events: subscribedEvents }
          }));
        }

        // Start ping interval
        enhancedDebug.debug('Starting ping interval (30s)', LogCategory.WEBSOCKET);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            enhancedDebug.trace('Sending ping', LogCategory.WEBSOCKET);
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);

        onConnect?.();
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          enhancedDebug.debug('WebSocket message received', LogCategory.WEBSOCKET, { type: message.type });

          if (message.type === 'event' && message.data) {
            const nexusEvent = message.data as NexusEvent;
            enhancedDebug.info('Event received', LogCategory.WEBSOCKET, {
              eventType: nexusEvent.event_type,
              groupId: nexusEvent.group_id,
              actorName: nexusEvent.actor_name,
            });

            setState(prev => ({
              ...prev,
              lastEvent: nexusEvent,
              eventHistory: [nexusEvent, ...prev.eventHistory].slice(0, 100),
            }));

            onEvent?.(nexusEvent);
          } else if (message.type === 'error') {
            const errorMsg = (message.data as any)?.message || 'Unknown error';
            const analysis = ErrorAnalyzer.analyze(new Error(errorMsg), { source: 'websocket' });
            enhancedDebug.error('WebSocket error message', new Error(errorMsg), LogCategory.WEBSOCKET, {
              analysis,
              message: errorMsg,
            });
            setState(prev => ({ ...prev, error: errorMsg }));
            onError?.(errorMsg);
          } else if (message.type === 'pong') {
            enhancedDebug.trace('Pong received', LogCategory.WEBSOCKET);
          }
        } catch (err) {
          enhancedDebug.error('Failed to parse WebSocket message', err, LogCategory.WEBSOCKET, {
            rawData: event.data?.substring(0, 200),
          });
        }
      };

      ws.onclose = (event) => {
        const closeReasons: Record<number, string> = {
          1000: 'Normal closure',
          1001: 'Going away',
          1006: 'Abnormal closure',
          1008: 'Policy violation',
          1011: 'Server error',
          1015: 'TLS handshake failure',
        };

        enhancedDebug.info('WebSocket closed', LogCategory.WEBSOCKET, {
          code: event.code,
          reason: event.reason || closeReasons[event.code] || 'Unknown',
          wasClean: event.wasClean,
        });

        setState(prev => ({ ...prev, connected: false, connecting: false }));

        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        onDisconnect?.();

        // Auto-reconnect after 5 seconds
        if (event.code !== 1000) {
          enhancedDebug.warn('Scheduling WebSocket reconnect', LogCategory.WEBSOCKET, {
            code: event.code,
            reason: closeReasons[event.code] || event.reason,
            fix: event.code === 1006
              ? 'Abnormal closure - check network and server'
              : event.code === 1011
              ? 'Server error - check server logs'
              : 'Will retry automatically',
          });
          reconnectTimeoutRef.current = setTimeout(() => {
            enhancedDebug.info('Attempting WebSocket reconnect', LogCategory.WEBSOCKET);
            connect();
          }, 5000);
        }
      };

      ws.onerror = (error) => {
        const analysis = ErrorAnalyzer.analyze(new Error('WebSocket error'), { source: 'websocket' });
        enhancedDebug.error(
          'WebSocket error',
          error instanceof Error ? error : new Error('WebSocket error'),
          LogCategory.WEBSOCKET,
          {
            analysis,
            fix: 'Check WebSocket server status and network connection',
            possibleCauses: [
              'Server is down',
              'Network blocked WebSocket',
              'Authentication token invalid',
              'Wrong WebSocket URL',
            ],
          }
        );
        setState(prev => ({ ...prev, error: 'WebSocket connection error', connecting: false }));
        onError?.('WebSocket connection error');
      };

    } catch (err: any) {
      const analysis = ErrorAnalyzer.analyze(err, { source: 'websocket_connect' });
      enhancedDebug.error(
        'WebSocket connection error',
        err,
        LogCategory.WEBSOCKET,
        { analysis, message: err.message }
      );
      setState(prev => ({ ...prev, error: err.message, connecting: false }));
      onError?.(err.message);
    }
  }, [getWebSocketUrl, subscribedEvents, onConnect, onDisconnect, onError, onEvent]);
  
  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    enhancedDebug.debug('=== WebSocket disconnect() called ===', LogCategory.WEBSOCKET);
    telegramDebug.logWebSocketEvent('disconnecting');
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    
    if (wsRef.current) {
      enhancedDebug.debug('Closing WebSocket connection (code: 1000)', LogCategory.WEBSOCKET);
      wsRef.current.close(1000); // Normal close
      wsRef.current = null;
    }
    
    setState(prev => ({ ...prev, connected: false }));
    enhancedDebug.debug('WebSocket disconnected', LogCategory.WEBSOCKET);
  }, []);
  
  // Send command through WebSocket
  const sendCommand = useCallback((action: string, params?: Record<string, any>) => {
    enhancedDebug.debug(`Sending command: ${action}`, LogCategory.WEBSOCKET, params);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        data: { action, params }
      }));
      enhancedDebug.debug(`Command sent: ${action}`, LogCategory.WEBSOCKET);
      return true;
    }
    enhancedDebug.error(`Command failed - WebSocket not open: ${action}`, null, LogCategory.WEBSOCKET, { action, params });
    return false;
  }, []);
  
  // Subscribe to specific events
  const subscribe = useCallback((events: EventType[]) => {
    enhancedDebug.debug('Subscribing to events:', LogCategory.WEBSOCKET, { events });
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        data: { events }
      }));
      enhancedDebug.debug('Subscribe message sent', LogCategory.WEBSOCKET);
      return true;
    }
    enhancedDebug.error('Subscribe failed - WebSocket not open', null, LogCategory.WEBSOCKET);
    return false;
  }, []);
  
  // Auto-connect on mount
  useEffect(() => {
    enhancedDebug.debug('=== useWebSocket useEffect ===', LogCategory.WEBSOCKET, { autoConnect, groupId });
    if (autoConnect) {
      connect();
    }
    
    return () => {
      enhancedDebug.debug('=== useWebSocket cleanup ===', LogCategory.WEBSOCKET);
      disconnect();
    };
  }, [autoConnect, connect, disconnect, groupId]);
  
  return {
    ...state,
    connect,
    disconnect,
    sendCommand,
    subscribe,
  };
}

export default useWebSocket;
