import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../../api/auth';

interface AutomationRule {
  rule_id: string;
  name: string;
  description?: string;
  conditions: any[];
  actions: any[];
  trigger_type: string;
  is_enabled: boolean;
  trigger_count: number;
  last_triggered?: string;
}

interface Tripwire {
  tripwire_id: string;
  name: string;
  trigger_behavior: string;
  escalation_levels: any[];
  window_seconds: number;
  is_enabled: boolean;
}

interface TimeRule {
  ruleset_id: string;
  name: string;
  schedule_type: string;
  days_of_week?: number[];
  start_time: string;
  end_time: string;
  config_overrides: any;
  is_active: boolean;
}

const AutomationCenter: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const [activeTab, setActiveTab] = useState('rules');
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [tripwires, setTripwires] = useState<Tripwire[]>([]);
  const [timeRules, setTimeRules] = useState<TimeRule[]>([]);
  
  // Form states
  const [showRuleForm, setShowRuleForm] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '',
    description: '',
    trigger_type: 'message',
    conditions: [{ field: '', operator: 'eq', value: '' }],
    actions: [{ type: 'delete', params: {} }],
    condition_logic: 'and',
  });

  useEffect(() => {
    if (groupId) {
      loadData();
    }
  }, [groupId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [rulesRes, tripwiresRes, timeRulesRes] = await Promise.all([
        api.get(`/api/v1/groups/${groupId}/automation-rules`),
        api.get(`/api/v1/groups/${groupId}/tripwires`),
        api.get(`/api/v1/groups/${groupId}/time-rules`),
      ]);
      setRules(rulesRes.data || []);
      setTripwires(tripwiresRes.data || []);
      setTimeRules(timeRulesRes.data || []);
    } catch (err) {
      console.error('Failed to load automation data:', err);
    } finally {
      setLoading(false);
    }
  };

  const createRule = async () => {
    try {
      await api.post(`/api/v1/groups/${groupId}/automation-rules`, newRule);
      setShowRuleForm(false);
      setNewRule({
        name: '',
        description: '',
        trigger_type: 'message',
        conditions: [{ field: '', operator: 'eq', value: '' }],
        actions: [{ type: 'delete', params: {} }],
        condition_logic: 'and',
      });
      loadData();
    } catch (err) {
      console.error('Failed to create rule:', err);
    }
  };

  const toggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await api.patch(`/api/v1/groups/${groupId}/automation-rules/${ruleId}`, {
        is_enabled: enabled,
      });
      loadData();
    } catch (err) {
      console.error('Failed to toggle rule:', err);
    }
  };

  const deleteRule = async (ruleId: string) => {
    try {
      await api.delete(`/api/v1/groups/${groupId}/automation-rules/${ruleId}`);
      loadData();
    } catch (err) {
      console.error('Failed to delete rule:', err);
    }
  };

  const addCondition = () => {
    setNewRule({
      ...newRule,
      conditions: [...newRule.conditions, { field: '', operator: 'eq', value: '' }],
    });
  };

  const removeCondition = (index: number) => {
    setNewRule({
      ...newRule,
      conditions: newRule.conditions.filter((_, i) => i !== index),
    });
  };

  const updateCondition = (index: number, field: string, value: any) => {
    const updated = [...newRule.conditions];
    updated[index] = { ...updated[index], [field]: value };
    setNewRule({ ...newRule, conditions: updated });
  };

  const addAction = () => {
    setNewRule({
      ...newRule,
      actions: [...newRule.actions, { type: 'delete', params: {} }],
    });
  };

  const removeAction = (index: number) => {
    setNewRule({
      ...newRule,
      actions: newRule.actions.filter((_, i) => i !== index),
    });
  };

  const updateAction = (index: number, field: string, value: any) => {
    const updated = [...newRule.actions];
    updated[index] = { ...updated[index], [field]: value };
    setNewRule({ ...newRule, actions: updated });
  };

  const triggerTypes = [
    { value: 'message', label: 'On Message' },
    { value: 'join', label: 'On Join' },
    { value: 'leave', label: 'On Leave' },
    { value: 'reaction', label: 'On Reaction' },
    { value: 'scheduled', label: 'Scheduled' },
  ];

  const conditionFields = [
    { value: 'trust_score', label: 'Trust Score' },
    { value: 'message_count', label: 'Message Count' },
    { value: 'account_age_days', label: 'Account Age (Days)' },
    { value: 'message_contains', label: 'Message Contains' },
    { value: 'has_link', label: 'Has Link' },
    { value: 'is_new_member', label: 'Is New Member' },
    { value: 'join_time', label: 'Join Time' },
    { value: 'user_role', label: 'User Role' },
  ];

  const operators = [
    { value: 'eq', label: 'Equals' },
    { value: 'ne', label: 'Not Equals' },
    { value: 'gt', label: 'Greater Than' },
    { value: 'lt', label: 'Less Than' },
    { value: 'gte', label: 'Greater or Equal' },
    { value: 'lte', label: 'Less or Equal' },
    { value: 'contains', label: 'Contains' },
    { value: 'matches', label: 'Matches Regex' },
    { value: 'in', label: 'In List' },
  ];

  const actionTypes = [
    { value: 'delete', label: 'Delete Message' },
    { value: 'mute', label: 'Mute User' },
    { value: 'warn', label: 'Warn User' },
    { value: 'kick', label: 'Kick User' },
    { value: 'ban', label: 'Ban User' },
    { value: 'notify_admins', label: 'Notify Admins' },
    { value: 'dm_user', label: 'Send DM' },
    { value: 'award_xp', label: 'Award XP' },
    { value: 'deduct_coins', label: 'Deduct Coins' },
    { value: 'add_role', label: 'Add Role' },
    { value: 'log', label: 'Log to Channel' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Automation Center</h1>
          <p className="text-dark-400 text-sm">Create powerful automation rules without coding</p>
        </div>
        <button
          onClick={() => setShowRuleForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center"
        >
          <span className="mr-2">+</span> New Rule
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-dark-800 p-1 rounded-lg">
        {[
          { id: 'rules', label: 'Automation Rules', icon: '⚡' },
          { id: 'tripwires', label: 'Tripwires', icon: '🚨' },
          { id: 'time', label: 'Time Rules', icon: '⏰' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center px-4 py-2 rounded-lg transition ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'text-dark-300 hover:text-white hover:bg-dark-700'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          {rules.length === 0 ? (
            <div className="bg-dark-800 rounded-lg p-8 text-center border border-dark-700">
              <p className="text-dark-400 mb-4">No automation rules yet</p>
              <button
                onClick={() => setShowRuleForm(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Your First Rule
              </button>
            </div>
          ) : (
            rules.map((rule) => (
              <div key={rule.rule_id} className="bg-dark-800 rounded-lg p-4 border border-dark-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        rule.is_enabled ? 'bg-green-500' : 'bg-dark-500'
                      }`}
                    ></div>
                    <div>
                      <h3 className="font-medium text-white">{rule.name}</h3>
                      <p className="text-dark-400 text-sm">
                        Trigger: {rule.trigger_type} • Triggered {rule.trigger_count} times
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleRule(rule.rule_id, !rule.is_enabled)}
                      className={`px-3 py-1 rounded text-sm ${
                        rule.is_enabled
                          ? 'bg-dark-600 text-dark-200'
                          : 'bg-green-600 text-white'
                      }`}
                    >
                      {rule.is_enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      onClick={() => deleteRule(rule.rule_id)}
                      className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {rule.description && (
                  <p className="text-dark-300 text-sm mt-2">{rule.description}</p>
                )}
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="px-2 py-1 bg-dark-700 text-dark-200 text-xs rounded">
                    {rule.conditions.length} conditions
                  </span>
                  <span className="px-2 py-1 bg-dark-700 text-dark-200 text-xs rounded">
                    {rule.actions.length} actions
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tripwires Tab */}
      {activeTab === 'tripwires' && (
        <div className="space-y-4">
          {tripwires.length === 0 ? (
            <div className="bg-dark-800 rounded-lg p-8 text-center border border-dark-700">
              <p className="text-dark-400">No tripwires configured</p>
              <p className="text-dark-500 text-sm mt-2">
                Tripwires automatically escalate when members trigger specific behaviors repeatedly.
              </p>
            </div>
          ) : (
            tripwires.map((tripwire) => (
              <div key={tripwire.tripwire_id} className="bg-dark-800 rounded-lg p-4 border border-dark-700">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-white">{tripwire.name}</h3>
                    <p className="text-dark-400 text-sm">
                      Triggers on: {tripwire.trigger_behavior}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      tripwire.is_enabled
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-dark-600 text-dark-300'
                    }`}
                  >
                    {tripwire.is_enabled ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="mt-4">
                  <p className="text-dark-400 text-xs mb-2">Escalation Levels:</p>
                  <div className="space-y-2">
                    {tripwire.escalation_levels.map((level, i) => (
                      <div key={i} className="flex items-center space-x-2 text-sm">
                        <span className="w-6 h-6 rounded-full bg-dark-600 flex items-center justify-center text-dark-200">
                          {i + 1}
                        </span>
                        <span className="text-dark-300">
                          At {level.threshold} triggers: {level.action}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Time Rules Tab */}
      {activeTab === 'time' && (
        <div className="space-y-4">
          {timeRules.length === 0 ? (
            <div className="bg-dark-800 rounded-lg p-8 text-center border border-dark-700">
              <p className="text-dark-400">No time-based rules configured</p>
              <p className="text-dark-500 text-sm mt-2">
                Create different rule sets for different times of day or week.
              </p>
            </div>
          ) : (
            timeRules.map((rule) => (
              <div key={rule.ruleset_id} className="bg-dark-800 rounded-lg p-4 border border-dark-700">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-white">{rule.name}</h3>
                    <p className="text-dark-400 text-sm">
                      {rule.start_time} - {rule.end_time}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      rule.is_active
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-dark-600 text-dark-300'
                    }`}
                  >
                    {rule.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {rule.days_of_week?.map((day) => (
                    <span
                      key={day}
                      className="w-6 h-6 rounded bg-blue-500/20 text-blue-400 text-xs flex items-center justify-center"
                    >
                      {['S', 'M', 'T', 'W', 'T', 'F', 'S'][day]}
                    </span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Rule Creation Modal */}
      {showRuleForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">Create Automation Rule</h2>
                <button
                  onClick={() => setShowRuleForm(false)}
                  className="text-dark-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-6">
                {/* Basic Info */}
                <div>
                  <label className="block text-dark-300 text-sm mb-2">Rule Name</label>
                  <input
                    type="text"
                    value={newRule.name}
                    onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="e.g., Auto-mute spammers"
                  />
                </div>

                <div>
                  <label className="block text-dark-300 text-sm mb-2">Description</label>
                  <textarea
                    value={newRule.description}
                    onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    rows={2}
                    placeholder="Describe what this rule does"
                  />
                </div>

                <div>
                  <label className="block text-dark-300 text-sm mb-2">Trigger Type</label>
                  <select
                    value={newRule.trigger_type}
                    onChange={(e) => setNewRule({ ...newRule, trigger_type: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    {triggerTypes.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Conditions */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-dark-300 text-sm">Conditions</label>
                    <button
                      onClick={addCondition}
                      className="text-blue-400 text-sm hover:text-blue-300"
                    >
                      + Add Condition
                    </button>
                  </div>
                  <div className="space-y-3">
                    {newRule.conditions.map((condition, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <select
                          value={condition.field}
                          onChange={(e) => updateCondition(index, 'field', e.target.value)}
                          className="flex-1 px-3 py-2 bg-dark-700 border border-dark-600 rounded text-white text-sm"
                        >
                          <option value="">Select field</option>
                          {conditionFields.map((f) => (
                            <option key={f.value} value={f.value}>
                              {f.label}
                            </option>
                          ))}
                        </select>
                        <select
                          value={condition.operator}
                          onChange={(e) => updateCondition(index, 'operator', e.target.value)}
                          className="px-3 py-2 bg-dark-700 border border-dark-600 rounded text-white text-sm"
                        >
                          {operators.map((o) => (
                            <option key={o.value} value={o.value}>
                              {o.label}
                            </option>
                          ))}
                        </select>
                        <input
                          type="text"
                          value={condition.value}
                          onChange={(e) => updateCondition(index, 'value', e.target.value)}
                          className="flex-1 px-3 py-2 bg-dark-700 border border-dark-600 rounded text-white text-sm"
                          placeholder="Value"
                        />
                        {newRule.conditions.length > 1 && (
                          <button
                            onClick={() => removeCondition(index)}
                            className="text-red-400 hover:text-red-300"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                  {newRule.conditions.length > 1 && (
                    <div className="mt-2 flex items-center space-x-2">
                      <span className="text-dark-400 text-sm">Logic:</span>
                      <select
                        value={newRule.condition_logic}
                        onChange={(e) => setNewRule({ ...newRule, condition_logic: e.target.value })}
                        className="px-3 py-1 bg-dark-700 border border-dark-600 rounded text-white text-sm"
                      >
                        <option value="and">All conditions (AND)</option>
                        <option value="or">Any condition (OR)</option>
                      </select>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-dark-300 text-sm">Actions</label>
                    <button
                      onClick={addAction}
                      className="text-blue-400 text-sm hover:text-blue-300"
                    >
                      + Add Action
                    </button>
                  </div>
                  <div className="space-y-3">
                    {newRule.actions.map((action, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <select
                          value={action.type}
                          onChange={(e) => updateAction(index, 'type', e.target.value)}
                          className="flex-1 px-3 py-2 bg-dark-700 border border-dark-600 rounded text-white text-sm"
                        >
                          {actionTypes.map((a) => (
                            <option key={a.value} value={a.value}>
                              {a.label}
                            </option>
                          ))}
                        </select>
                        {newRule.actions.length > 1 && (
                          <button
                            onClick={() => removeAction(index)}
                            className="text-red-400 hover:text-red-300"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Buttons */}
                <div className="flex justify-end space-x-3 pt-4 border-t border-dark-700">
                  <button
                    onClick={() => setShowRuleForm(false)}
                    className="px-4 py-2 bg-dark-600 text-dark-200 rounded-lg hover:bg-dark-500"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={createRule}
                    disabled={!newRule.name}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Create Rule
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomationCenter;
