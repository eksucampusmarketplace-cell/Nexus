import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../../api/auth';

interface PredictiveScore {
  user_id: number;
  risk_score: number;
  spam_likelihood: number;
  raid_likelihood: number;
  abuse_likelihood: number;
  matched_patterns: string[];
  behavioral_flags: string[];
  monitoring_level: number;
  shadow_watch: boolean;
}

interface Anomaly {
  anomaly_id: string;
  anomaly_type: string;
  title: string;
  description: string;
  severity: number;
  detected_at: string;
  action_taken?: string;
  resolved_at?: string;
}

interface ConversationNode {
  user_id: number;
  influence_score: number;
  centrality_score: number;
  messages_sent: number;
  replies_received: number;
  is_isolated: boolean;
}

interface Topic {
  cluster_id: string;
  name: string;
  keywords: string[];
  messages_24h: number;
  is_emerging: boolean;
  is_dying: boolean;
  is_controversial: boolean;
}

interface ChurnPrediction {
  user_id: number;
  churn_risk: number;
  days_inactive: number;
  suggested_intervention?: string;
}

const GroupIntelligence: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [predictiveStats, setPredictiveStats] = useState<any>({});
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [influencers, setInfluencers] = useState<ConversationNode[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [churnRisks, setChurnRisks] = useState<ChurnPrediction[]>([]);
  const [riskScores, setRiskScores] = useState<PredictiveScore[]>([]);

  useEffect(() => {
    if (groupId) {
      loadData();
    }
  }, [groupId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const overview = await api.get(`/api/v1/groups/${groupId}/intelligence`);
      setPredictiveStats(overview.data.predictive_moderation || {});
      setAnomalies(overview.data.anomaly_timeline?.anomalies || []);
      setTopics(overview.data.topic_intelligence?.topics || []);
      setChurnRisks(overview.data.churn_predictions?.at_risk_members || []);

      // Load conversation graph
      const graph = await api.get(`/api/v1/groups/${groupId}/conversation-graph`);
      setInfluencers(graph.data.nodes?.slice(0, 10) || []);

      // Load risk scores
      const scores = await api.get(`/api/v1/groups/${groupId}/predictive-scores?min_risk=20`);
      setRiskScores(scores.data || []);
    } catch (err: any) {
      console.error('Failed to load intelligence data:', err);
      setError(err.response?.data?.detail || 'Failed to load intelligence data');
    } finally {
      setLoading(false);
    }
  };

  const resolveAnomaly = async (anomalyId: string, action: string) => {
    try {
      await api.post(`/api/v1/groups/${groupId}/anomalies/${anomalyId}/resolve`, {
        action_taken: action,
      });
      loadData();
    } catch (err) {
      console.error('Failed to resolve anomaly:', err);
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 70) return 'text-red-400';
    if (score >= 40) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getRiskBg = (score: number) => {
    if (score >= 70) return 'bg-red-500/20 border-red-500/30';
    if (score >= 40) return 'bg-yellow-500/20 border-yellow-500/30';
    return 'bg-green-500/20 border-green-500/30';
  };

  const getSeverityColor = (severity: number) => {
    if (severity >= 4) return 'bg-red-500';
    if (severity >= 3) return 'bg-orange-500';
    if (severity >= 2) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
        <p className="text-red-400">{error}</p>
        <button
          onClick={loadData}
          className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Group Intelligence</h1>
          <p className="text-dark-400 text-sm">AI-powered community insights and predictions</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Refresh
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-dark-800 p-1 rounded-lg overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview', icon: '📊' },
          { id: 'predictive', label: 'Predictive', icon: '🔮' },
          { id: 'anomalies', label: 'Anomalies', icon: '⚠️' },
          { id: 'graph', label: 'Social Graph', icon: '🕸️' },
          { id: 'topics', label: 'Topics', icon: '💬' },
          { id: 'churn', label: 'Churn Risk', icon: '📉' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center px-4 py-2 rounded-lg transition whitespace-nowrap ${
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

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
              <div className="flex items-center justify-between">
                <span className="text-dark-400">High Risk Members</span>
                <span className="text-2xl">🔴</span>
              </div>
              <p className="text-3xl font-bold text-red-400 mt-2">
                {predictiveStats.high_risk_count || 0}
              </p>
            </div>

            <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
              <div className="flex items-center justify-between">
                <span className="text-dark-400">Medium Risk</span>
                <span className="text-2xl">🟡</span>
              </div>
              <p className="text-3xl font-bold text-yellow-400 mt-2">
                {predictiveStats.medium_risk_count || 0}
              </p>
            </div>

            <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
              <div className="flex items-center justify-between">
                <span className="text-dark-400">Shadow Watch</span>
                <span className="text-2xl">👁️</span>
              </div>
              <p className="text-3xl font-bold text-purple-400 mt-2">
                {predictiveStats.shadow_watch_count || 0}
              </p>
            </div>

            <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
              <div className="flex items-center justify-between">
                <span className="text-dark-400">Recent Anomalies</span>
                <span className="text-2xl">⚠️</span>
              </div>
              <p className="text-3xl font-bold text-orange-400 mt-2">
                {anomalies.filter(a => !a.resolved_at).length}
              </p>
            </div>
          </div>

          {/* Recent Anomalies */}
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Anomalies</h3>
            {anomalies.length === 0 ? (
              <p className="text-dark-400">No anomalies detected in the last 7 days.</p>
            ) : (
              <div className="space-y-3">
                {anomalies.slice(0, 5).map((anomaly) => (
                  <div
                    key={anomaly.anomaly_id}
                    className={`p-4 rounded-lg border ${getRiskBg(anomaly.severity * 20)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span
                            className={`w-3 h-3 rounded-full ${getSeverityColor(anomaly.severity)}`}
                          ></span>
                          <span className="font-medium text-white">{anomaly.title}</span>
                        </div>
                        <p className="text-dark-300 text-sm mt-1">{anomaly.description}</p>
                      </div>
                      <span className="text-dark-400 text-xs">
                        {new Date(anomaly.detected_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Trending Topics */}
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold text-white mb-4">Trending Topics</h3>
            <div className="flex flex-wrap gap-2">
              {topics.slice(0, 10).map((topic) => (
                <div
                  key={topic.cluster_id}
                  className={`px-3 py-2 rounded-full text-sm ${
                    topic.is_emerging
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                      : topic.is_controversial
                      ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                      : 'bg-dark-700 text-dark-200'
                  }`}
                >
                  {topic.is_emerging && '📈 '}
                  {topic.is_controversial && '🔥 '}
                  {topic.name}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Predictive Tab */}
      {activeTab === 'predictive' && (
        <div className="space-y-6">
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold text-white mb-4">Risk Assessment</h3>
            <div className="space-y-3">
              {riskScores.length === 0 ? (
                <p className="text-dark-400">No members flagged for risk at this time.</p>
              ) : (
                riskScores.map((score) => (
                  <div
                    key={score.user_id}
                    className="flex items-center justify-between p-4 bg-dark-700 rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${getRiskBg(
                          score.risk_score
                        )}`}
                      >
                        {score.risk_score}
                      </div>
                      <div>
                        <p className="font-medium text-white">User #{score.user_id}</p>
                        <div className="flex space-x-3 text-xs text-dark-400 mt-1">
                          <span>Spam: {(score.spam_likelihood * 100).toFixed(0)}%</span>
                          <span>Raid: {(score.raid_likelihood * 100).toFixed(0)}%</span>
                          <span>Abuse: {(score.abuse_likelihood * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {score.behavioral_flags.map((flag) => (
                        <span
                          key={flag}
                          className="px-2 py-1 bg-dark-600 text-xs rounded text-dark-200"
                        >
                          {flag}
                        </span>
                      ))}
                      {score.shadow_watch && (
                        <span className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs rounded">
                          Shadow Watch
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Anomalies Tab */}
      {activeTab === 'anomalies' && (
        <div className="space-y-6">
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold text-white mb-4">Anomaly Timeline</h3>
            <div className="space-y-4">
              {anomalies.length === 0 ? (
                <p className="text-dark-400">No anomalies detected.</p>
              ) : (
                anomalies.map((anomaly) => (
                  <div
                    key={anomaly.anomaly_id}
                    className={`p-4 rounded-lg border ${
                      anomaly.resolved_at
                        ? 'bg-dark-700/50 border-dark-600'
                        : getRiskBg(anomaly.severity * 20)
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-3">
                          <span
                            className={`w-3 h-3 rounded-full ${getSeverityColor(anomaly.severity)}`}
                          ></span>
                          <span className="font-medium text-white">{anomaly.title}</span>
                          {anomaly.resolved_at ? (
                            <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded">
                              Resolved
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 bg-orange-500/20 text-orange-400 text-xs rounded">
                              Active
                            </span>
                          )}
                        </div>
                        <p className="text-dark-300 text-sm mt-2">{anomaly.description}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-dark-400">
                          <span>Type: {anomaly.anomaly_type}</span>
                          <span>Detected: {new Date(anomaly.detected_at).toLocaleString()}</span>
                        </div>
                      </div>
                      {!anomaly.resolved_at && (
                        <button
                          onClick={() => resolveAnomaly(anomaly.anomaly_id, 'Acknowledged')}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Social Graph Tab */}
      {activeTab === 'graph' && (
        <div className="space-y-6">
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold text-white mb-4">Top Influencers</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {influencers
                .sort((a, b) => b.influence_score - a.influence_score)
                .slice(0, 9)
                .map((node, index) => (
                  <div key={node.user_id} className="p-4 bg-dark-700 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                        #{index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-white">User #{node.user_id}</p>
                        <div className="flex space-x-2 text-xs text-dark-400">
                          <span>Influence: {node.influence_score.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="p-2 bg-dark-600 rounded">
                        <p className="text-dark-400">Messages</p>
                        <p className="text-white font-medium">{node.messages_sent}</p>
                      </div>
                      <div className="p-2 bg-dark-600 rounded">
                        <p className="text-dark-400">Replies</p>
                        <p className="text-white font-medium">{node.replies_received}</p>
                      </div>
                      <div className="p-2 bg-dark-600 rounded">
                        <p className="text-dark-400">Centrality</p>
                        <p className="text-white font-medium">{node.centrality_score.toFixed(2)}</p>
                      </div>
                    </div>
                    {node.is_isolated && (
                      <p className="mt-2 text-xs text-yellow-400">⚠️ Isolated member</p>
                    )}
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Topics Tab */}
      {activeTab === 'topics' && (
        <div className="space-y-6">
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold text-white mb-4">Topic Intelligence</h3>
            <div className="space-y-4">
              {topics.length === 0 ? (
                <p className="text-dark-400">No topic data available yet.</p>
              ) : (
                topics.map((topic) => (
                  <div key={topic.cluster_id} className="p-4 bg-dark-700 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="text-xl">
                          {topic.is_emerging ? '📈' : topic.is_dying ? '📉' : '💬'}
                        </span>
                        <span className="font-medium text-white">{topic.name}</span>
                        {topic.is_controversial && (
                          <span className="text-red-400">🔥</span>
                        )}
                      </div>
                      <span className="text-dark-400 text-sm">{topic.messages_24h} msg/24h</span>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {topic.keywords.slice(0, 5).map((keyword, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-dark-600 text-dark-200 text-xs rounded"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Churn Risk Tab */}
      {activeTab === 'churn' && (
        <div className="space-y-6">
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold text-white mb-4">Churn Risk Analysis</h3>
            <div className="space-y-4">
              {churnRisks.length === 0 ? (
                <p className="text-dark-400">No members currently at churn risk.</p>
              ) : (
                churnRisks.map((member) => (
                  <div key={member.user_id} className="p-4 bg-dark-700 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div
                          className={`w-12 h-12 rounded-full flex items-center justify-center ${
                            member.churn_risk >= 0.7
                              ? 'bg-red-500/20 text-red-400'
                              : member.churn_risk >= 0.4
                              ? 'bg-yellow-500/20 text-yellow-400'
                              : 'bg-green-500/20 text-green-400'
                          }`}
                        >
                          {(member.churn_risk * 100).toFixed(0)}%
                        </div>
                        <div>
                          <p className="font-medium text-white">User #{member.user_id}</p>
                          <p className="text-dark-400 text-sm">
                            Inactive for {member.days_inactive} days
                          </p>
                        </div>
                      </div>
                    </div>
                    {member.suggested_intervention && (
                      <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded">
                        <p className="text-blue-400 text-sm">
                          💡 Suggested: {member.suggested_intervention}
                        </p>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupIntelligence;
