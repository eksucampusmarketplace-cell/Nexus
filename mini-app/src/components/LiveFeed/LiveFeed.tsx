/**
 * Live Feed Component - Real-time message stream from the group.
 * 
 * Shows messages coming in, who is sending them, their trust score
 * and level, and allows taking moderation actions directly.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useWebSocket, NexusEvent, EventTypes } from '../hooks/useWebSocket';
import { api } from '../api/client';

interface Message {
  id: number;
  message_id: number;
  sender_id: number;
  sender_telegram_id: number;
  sender_name: string;
  sender_username?: string;
  sender_photo_url?: string;
  content?: string;
  content_type: string;
  timestamp: string;
  trust_score: number;
  level: number;
  
  // For AI-flagged messages
  ai_flagged?: boolean;
  ai_confidence?: number;
  ai_reason?: string;
}

interface Member {
  id: number;
  telegram_id: number;
  name: string;
  username?: string;
  photo_url?: string;
  trust_score: number;
  level: number;
  warn_count: number;
  is_muted: boolean;
  is_banned: boolean;
}

interface LiveFeedProps {
  groupId: number;
  userId?: number;
  telegramId?: number;
  username?: string;
  maxHeight?: string;
  showActions?: boolean;
}

export default function LiveFeed({
  groupId,
  userId,
  telegramId,
  username,
  maxHeight = '600px',
  showActions = true,
}: LiveFeedProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [showActionCard, setShowActionCard] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'flagged' | 'members'>('all');
  
  const feedRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  
  // WebSocket connection
  const {
    connected,
    connecting,
    error,
    lastEvent,
    sendCommand,
  } = useWebSocket({
    groupId,
    userId,
    telegramId,
    username,
    autoConnect: true,
    onEvent: (event) => {
      // Handle new messages
      if (event.event_type === EventTypes.MESSAGE_NEW) {
        handleNewMessage(event);
      } else if (event.event_type === EventTypes.MESSAGE_DELETED) {
        handleMessageDeleted(event);
      } else if (event.event_type === EventTypes.AI_FLAGGED) {
        handleAIFlagged(event);
      }
    },
  });
  
  // Handle new message event
  const handleNewMessage = useCallback((event: NexusEvent) => {
    const msg: Message = {
      id: event.event_id,
      message_id: event.message_id || 0,
      sender_id: event.actor_id || 0,
      sender_telegram_id: event.actor_telegram_id || 0,
      sender_name: event.actor_name || 'Unknown',
      content: event.data?.content || '',
      content_type: event.data?.content_type || 'text',
      timestamp: event.timestamp,
      trust_score: event.data?.trust_score || 50,
      level: event.data?.level || 1,
    };
    
    setMessages(prev => [msg, ...prev].slice(0, 500)); // Keep last 500 messages
  }, []);
  
  // Handle message deleted event
  const handleMessageDeleted = useCallback((event: NexusEvent) => {
    const messageId = event.message_id;
    if (messageId) {
      setMessages(prev => prev.filter(m => m.message_id !== messageId));
    }
  }, []);
  
  // Handle AI flagged event
  const handleAIFlagged = useCallback((event: NexusEvent) => {
    const messageId = event.message_id;
    if (messageId) {
      setMessages(prev => prev.map(m => {
        if (m.message_id === messageId) {
          return {
            ...m,
            ai_flagged: true,
            ai_confidence: event.ai_confidence,
            ai_reason: event.reason,
          };
        }
        return m;
      }));
    }
  }, []);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && feedRef.current) {
      // For newest-on-top, we don't need to scroll
    }
  }, [messages, autoScroll]);
  
  // Handle message click - show action card
  const handleMessageClick = async (message: Message) => {
    setSelectedMessage(message);
    
    try {
      // Fetch member details
      const response = await api.get(`/api/v1/groups/${groupId}/members/${message.sender_id}`);
      setSelectedMember(response.data);
      setShowActionCard(true);
    } catch (err) {
      console.error('Failed to fetch member details:', err);
      // Show basic action card with message info
      setSelectedMember({
        id: message.sender_id,
        telegram_id: message.sender_telegram_id,
        name: message.sender_name,
        trust_score: message.trust_score,
        level: message.level,
        warn_count: 0,
        is_muted: false,
        is_banned: false,
      });
      setShowActionCard(true);
    }
  };
  
  // Moderation actions
  const handleAction = async (action: string, params?: Record<string, any>) => {
    if (!selectedMember) return;
    
    setActionLoading(true);
    try {
      // Use WebSocket command for real-time execution
      const success = sendCommand(action, {
        target_id: selectedMember.id,
        target_telegram_id: selectedMember.telegram_id,
        ...params,
      });
      
      if (!success) {
        // Fallback to API
        await api.post(`/api/v1/groups/${groupId}/moderation/${action}`, {
          target_id: selectedMember.id,
          ...params,
        });
      }
      
      // Close action card after successful action
      setTimeout(() => {
        setShowActionCard(false);
        setSelectedMessage(null);
        setSelectedMember(null);
      }, 1000);
    } catch (err) {
      console.error(`Failed to ${action}:`, err);
    } finally {
      setActionLoading(false);
    }
  };
  
  // Filter messages
  const filteredMessages = messages.filter(msg => {
    if (filter === 'flagged') return msg.ai_flagged;
    if (filter === 'members') return true; // Would filter by actual members
    return true;
  });
  
  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Get trust score color
  const getTrustColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-green-300';
    if (score >= 40) return 'text-yellow-400';
    if (score >= 20) return 'text-orange-400';
    return 'text-red-400';
  };
  
  return (
    <div className="flex flex-col h-full" style={{ maxHeight }}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-700">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-white">Live Feed</h3>
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : connecting ? 'bg-yellow-500' : 'bg-red-500'}`} />
          <span className="text-xs text-dark-400">
            {connected ? 'Connected' : connecting ? 'Connecting...' : 'Disconnected'}
          </span>
        </div>
        
        {/* Filter */}
        <div className="flex gap-1">
          {(['all', 'flagged'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                filter === f
                  ? 'bg-blue-600 text-white'
                  : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
              }`}
            >
              {f === 'all' ? 'All' : 'AI Flagged'}
            </button>
          ))}
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <div className="px-4 py-2 bg-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}
      
      {/* Message feed */}
      <div ref={feedRef} className="flex-1 overflow-y-auto p-4 space-y-2">
        {filteredMessages.length === 0 ? (
          <div className="text-center text-dark-400 py-8">
            <p>No messages yet</p>
            <p className="text-xs mt-1">Messages will appear here in real-time</p>
          </div>
        ) : (
          filteredMessages.map(msg => (
            <div
              key={msg.id}
              onClick={() => handleMessageClick(msg)}
              className={`p-3 rounded-lg cursor-pointer transition-all hover:bg-dark-700 ${
                msg.ai_flagged ? 'border border-red-500/50 bg-red-500/10' : 'bg-dark-800'
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Avatar */}
                <div className="w-10 h-10 rounded-full bg-dark-600 flex items-center justify-center text-lg">
                  {msg.sender_name.charAt(0).toUpperCase()}
                </div>
                
                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-white truncate">
                      {msg.sender_name}
                    </span>
                    
                    {/* Trust score */}
                    <span className={`text-xs ${getTrustColor(msg.trust_score)}`}>
                      TS: {msg.trust_score}
                    </span>
                    
                    {/* Level */}
                    <span className="text-xs text-purple-400">
                      Lv.{msg.level}
                    </span>
                    
                    {/* Time */}
                    <span className="text-xs text-dark-500 ml-auto">
                      {formatTime(msg.timestamp)}
                    </span>
                  </div>
                  
                  {/* Content */}
                  {msg.content && (
                    <p className="text-sm text-dark-200 break-words">
                      {msg.content}
                    </p>
                  )}
                  
                  {/* AI flag badge */}
                  {msg.ai_flagged && (
                    <div className="mt-2 flex items-center gap-2">
                      <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">
                        AI Flagged
                      </span>
                      {msg.ai_confidence && (
                        <span className="text-xs text-dark-400">
                          Confidence: {(msg.ai_confidence * 100).toFixed(0)}%
                        </span>
                      )}
                      {msg.ai_reason && (
                        <span className="text-xs text-dark-400">
                          Reason: {msg.ai_reason}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* Floating Action Card */}
      {showActionCard && selectedMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-dark-800 rounded-xl shadow-xl max-w-sm w-full mx-4 overflow-hidden">
            {/* Member header */}
            <div className="p-4 border-b border-dark-700">
              <div className="flex items-center gap-3">
                <div className="w-14 h-14 rounded-full bg-dark-600 flex items-center justify-center text-2xl">
                  {selectedMember.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h4 className="font-semibold text-white">{selectedMember.name}</h4>
                  <div className="flex items-center gap-3 text-sm">
                    <span className={getTrustColor(selectedMember.trust_score)}>
                      Trust: {selectedMember.trust_score}
                    </span>
                    <span className="text-purple-400">Level {selectedMember.level}</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Member stats */}
            <div className="p-4 grid grid-cols-3 gap-2 text-center border-b border-dark-700">
              <div className="bg-dark-700 rounded-lg p-2">
                <div className="text-lg font-bold text-yellow-400">{selectedMember.warn_count}</div>
                <div className="text-xs text-dark-400">Warnings</div>
              </div>
              <div className="bg-dark-700 rounded-lg p-2">
                <div className={`text-lg font-bold ${selectedMember.is_muted ? 'text-red-400' : 'text-green-400'}`}>
                  {selectedMember.is_muted ? 'Muted' : 'Active'}
                </div>
                <div className="text-xs text-dark-400">Status</div>
              </div>
              <div className="bg-dark-700 rounded-lg p-2">
                <div className={`text-lg font-bold ${selectedMember.is_banned ? 'text-red-400' : 'text-green-400'}`}>
                  {selectedMember.is_banned ? 'Banned' : 'OK'}
                </div>
                <div className="text-xs text-dark-400">Ban Status</div>
              </div>
            </div>
            
            {/* Action buttons */}
            {showActions && (
              <div className="p-4 grid grid-cols-3 gap-2">
                <button
                  onClick={() => handleAction('warn', { reason: 'From Live Feed' })}
                  disabled={actionLoading}
                  className="p-3 bg-yellow-500/20 text-yellow-400 rounded-lg hover:bg-yellow-500/30 transition-colors disabled:opacity-50"
                >
                  ⚠️ Warn
                </button>
                <button
                  onClick={() => handleAction('mute', { duration_seconds: 3600 })}
                  disabled={actionLoading}
                  className="p-3 bg-orange-500/20 text-orange-400 rounded-lg hover:bg-orange-500/30 transition-colors disabled:opacity-50"
                >
                  🔇 Mute
                </button>
                <button
                  onClick={() => handleAction('ban', { reason: 'From Live Feed' })}
                  disabled={actionLoading}
                  className="p-3 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50"
                >
                  🚫 Ban
                </button>
              </div>
            )}
            
            {/* Close button */}
            <button
              onClick={() => {
                setShowActionCard(false);
                setSelectedMessage(null);
                setSelectedMember(null);
              }}
              className="w-full p-3 text-dark-400 hover:bg-dark-700 transition-colors text-sm"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
