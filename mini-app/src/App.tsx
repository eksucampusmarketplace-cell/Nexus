import { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useGroupStore } from './stores/groupStore'
import { telegramAuth } from './api/auth'
import { getGroupByTelegramId, getGroupStatsByTelegramId } from './api/groups'

// Enhanced Debug System - Import both old and new for compatibility
import {
  enhancedDebug,
  telegramDebug,
  InitDataValidator,
  ErrorAnalyzer,
  ErrorCode,
  LogCategory,
  LogLevel,
} from './utils/enhancedDebug'

// Backward compatibility imports
import {
  debugLog,
  logInitData,
  logAuthState,
  logTelegramEvent
} from './utils/debug'

// Layouts
import MainLayout from './components/Layout/MainLayout'

// Views
import Dashboard from './views/Dashboard'
import Help from './views/Help'
import AdminDashboard from './views/AdminDashboard/AdminDashboard'
import MemberProfile from './views/MemberView/MemberProfile'
import Modules from './views/AdminDashboard/Modules'
import Members from './views/AdminDashboard/Members'
import Analytics from './views/AdminDashboard/Analytics'
import Scheduler from './views/AdminDashboard/Scheduler'
import Settings from './views/AdminDashboard/Settings'
import Economy from './views/AdminDashboard/Economy'
import BotBuilder from './views/AdminDashboard/BotBuilder'
import AdvancedFeatures from './views/AdminDashboard/AdvancedFeatures'
import ModerationQueue from './views/AdminDashboard/ModerationQueue'
import NotesAndFilters from './views/AdminDashboard/NotesAndFilters'
import Locks from './views/AdminDashboard/Locks'
import AntiSpam from './views/AdminDashboard/AntiSpam'
import RulesAndGreetings from './views/AdminDashboard/RulesAndGreetings'
import ImportExport from './views/AdminDashboard/ImportExport'
import CustomBotToken from './views/AdminDashboard/CustomBotToken'
import PollsCenter from './views/AdminDashboard/PollsCenter'
import SecurityCenter from './views/AdminDashboard/SecurityCenter'
import Loading from './components/UI/Loading'
import Integrations from './views/AdminDashboard/Integrations'
import GamificationHub from './views/AdminDashboard/GamificationHub'
import CommunityHub from './views/AdminDashboard/CommunityHub'
import GamesHub from './views/AdminDashboard/GamesHub'
import BroadcastCenter from './views/AdminDashboard/BroadcastCenter'
import AutomationCenter from './views/AdminDashboard/AutomationCenter'
import FormattingTools from './views/AdminDashboard/FormattingTools'
import AdvancedSearch from './views/AdminDashboard/AdvancedSearch'
import Graveyard from './views/AdminDashboard/Graveyard'

// New Intelligence Views
import GroupIntelligence from './views/AdminDashboard/GroupIntelligence'
import AutomationCenterEnhanced from './views/AdminDashboard/AutomationCenterEnhanced'

function App() {
  const { isAuthenticated, isLoading, isRehydrated, error, setAuth, setLoading, setError } = useAuthStore()
  const { currentGroup, setCurrentGroup } = useGroupStore()
  const [initData, setInitData] = useState<string>('')
  const [errorDetail, setErrorDetail] = useState<string>('')
  const [authAttempted, setAuthAttempted] = useState(false)
  const [dbGroupId, setDbGroupId] = useState<number | null>(null) // Store the Database Group ID

  useEffect(() => {
    const init = async () => {
      // Use enhanced debug system with full diagnostics
      await enhancedDebug.withContext('App Initialization', LogCategory.INIT, async (ctx) => {
        ctx.log('Starting app initialization');
        setLoading(true);
        telegramDebug.logAuthEvent('initializing');

        // Get Telegram WebApp object
        const tg = (window as any).Telegram?.WebApp;

        // Enhanced Telegram diagnostics
        telegramDebug.logInitData((window as any).Telegram);

        // Validate initData with detailed diagnostics
        const botToken = import.meta.env.VITE_BOT_TOKEN || ''; // Only for client-side diagnostics
        const validationResult = InitDataValidator.validate(tg?.initData, botToken);

        if (!validationResult.valid) {
          enhancedDebug.warn('initData validation issues detected', LogCategory.INIT, validationResult);

          // Check for specific private chat issue
          if (!validationResult.initDataPresent) {
            const diagnosis = InitDataValidator.diagnoseMissingInitData((window as any).Telegram);
            enhancedDebug.warn('Missing initData diagnosis', LogCategory.TELEGRAM, diagnosis);

            // Provide actionable guidance to user
            if (diagnosis.inTelegram && diagnosis.chatType === 'private') {
              setError('Open from Group');
              setErrorDetail('The Mini App works best when opened from a group. Please:\n1. Add the bot to a group\n2. Open the Mini App from that group\n\nReason: Telegram does not provide group context in private chats.');
              setAuthAttempted(true);
              setLoading(false);
              return;
            }
          }
        }

        // Configure Telegram WebApp theme to match our dark theme
        if (tg) {
          const version = parseFloat(tg.version || '6.0');
          enhancedDebug.debug(`WebApp version: ${version}`, LogCategory.TELEGRAM);

          if (version >= 6.1) {
            try {
              tg.setHeaderColor('#020617');
              tg.setBottomBarColor('#020617');
              tg.setBackgroundColor('#020617');
              enhancedDebug.success('Theme colors set successfully', LogCategory.TELEGRAM);
            } catch (e) {
              enhancedDebug.warn('Color settings not supported', LogCategory.TELEGRAM, e);
            }
          }

          tg.expand();

          // Set up event listeners
          tg.onEvent('viewportChanged', (data: any) => {
            telegramDebug.logWebSocketEvent('viewportChanged', data);
          });
          tg.onEvent('themeChanged', () => {
            telegramDebug.logWebSocketEvent('themeChanged', { colorScheme: tg.colorScheme });
          });
        }

        // Wait for initData with enhanced logging
        let initDataRaw = tg?.initData || '';
        let attempts = 0;
        const maxAttempts = 20;

        enhancedDebug.debug(`Starting initData wait loop. Initial: ${initDataRaw ? 'Present' : 'Empty'}`, LogCategory.INIT);

        while (!initDataRaw && tg && attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 100));
          initDataRaw = tg?.initData || '';
          attempts++;
          if (initDataRaw) {
            ctx.log(`initData became available after ${attempts} attempts`);
            telegramDebug.logInitData((window as any).Telegram);
          }
        }

        enhancedDebug.debug(`Wait loop complete. attempts=${attempts}, hasInitData=${!!initDataRaw}`, LogCategory.INIT);
        setInitData(initDataRaw);

        if (!initDataRaw) {
          enhancedDebug.warn('No initData available after waiting', LogCategory.INIT);

          const storedToken = localStorage.getItem('nexus_token');
          enhancedDebug.debug('Checking for stored token', LogCategory.TOKEN, { found: !!storedToken });

          if (storedToken) {
            enhancedDebug.success('Found stored token, allowing access', LogCategory.AUTH);
            telegramDebug.logAuthEvent('restored_from_storage');
            setAuthAttempted(true);
            setLoading(false);
            return;
          }

          // Enhanced error message with fix suggestion
          const diagnosis = InitDataValidator.diagnoseMissingInitData((window as any).Telegram);
          enhancedDebug.error(
            'Authentication Failed - No initData',
            new Error(ErrorCode.MISSING_INIT_DATA),
            LogCategory.AUTH,
            diagnosis
          );

          setError('Authentication Failed');
          setErrorDetail(`No Telegram authentication data available.\n\n${diagnosis.explanation}\n\nTo fix:\n${diagnosis.workarounds.join('\n')}`);
          setAuthAttempted(true);
          setLoading(false);
          return;
        }

        // Get Telegram Chat ID from start_param or chat
        // IMPORTANT: Keep as string to avoid JavaScript number precision loss
        // Telegram IDs can exceed Number.MAX_SAFE_INTEGER (2^53-1)
        const startParam = tg?.initDataUnsafe?.start_param;
        const chatId = tg?.initDataUnsafe?.chat?.id;
        const groupIdStr = startParam ? String(startParam) : (chatId ? String(chatId) : null);
        const telegramChatId = groupIdStr ? Number(groupIdStr) : null;

        enhancedDebug.debug(`Extracted IDs`, LogCategory.GROUPS, {
          startParam,
          chatId,
          telegramChatId,
          chatType: tg?.initDataUnsafe?.chat?.type,
        });

        try {
          // Authenticate with backend
          enhancedDebug.info('Starting authentication with backend', LogCategory.AUTH);
          telegramDebug.logAuthEvent('authenticating');

          enhancedDebug.debug('Init data being sent', LogCategory.AUTH, {
            length: initDataRaw.length,
            preview: initDataRaw.substring(0, 200),
          });

          const authData = await telegramAuth(initDataRaw);

          enhancedDebug.success('Authentication successful!', LogCategory.AUTH, {
            userId: authData.user?.id,
            username: authData.user?.username,
          });
          telegramDebug.logAuthEvent('authenticated');

          enhancedDebug.debug('Received access token', LogCategory.TOKEN, {
            preview: authData.access_token?.substring(0, 30),
          });

          setAuth(authData.access_token, authData.user);
          enhancedDebug.debug('Auth state set in store', LogCategory.AUTH);

          // If we have a Telegram Chat ID, resolve it to Database Group ID
          if (telegramChatId) {
            try {
              enhancedDebug.info(`Resolving Telegram Chat ID ${telegramChatId}`, LogCategory.GROUPS);
              const group = await getGroupByTelegramId(telegramChatId);
              setDbGroupId(group.id);
              setCurrentGroup(group);
              enhancedDebug.success(`Resolved to Database Group ID: ${group.id}`, LogCategory.GROUPS, {
                groupTitle: group.title,
              });
            } catch (e: any) {
              const errorAnalysis = ErrorAnalyzer.analyze(e, { telegramChatId });
              enhancedDebug.error(
                'Failed to resolve Telegram Chat ID',
                e,
                LogCategory.GROUPS,
                { analysis: errorAnalysis, telegramChatId }
              );
              // Don't fail auth, just log it
            }
          } else {
            enhancedDebug.warn('No telegramChatId available, skipping group resolution', LogCategory.GROUPS);
          }
        } catch (err: any) {
          const errorAnalysis = ErrorAnalyzer.analyze(err, { initDataLength: initDataRaw.length });
          enhancedDebug.error('Authentication error', err, LogCategory.AUTH, {
            analysis: errorAnalysis,
            responseData: err.response?.data,
            status: err.response?.status,
          });
          telegramDebug.logAuthError(err, { initDataLength: initDataRaw.length });

          const detail = err.response?.data?.detail || 'Authentication failed';
          setError('Authentication Failed');
          setErrorDetail(`${detail}\n\n${errorAnalysis.fix}`);
        }

        setAuthAttempted(true);
        setLoading(false);
        enhancedDebug.info('=== APP INITIALIZATION COMPLETE ===', LogCategory.INIT, {
          authAttempted: true,
          isLoading: false,
          isAuthenticated: useAuthStore.getState().isAuthenticated,
        });
      });
    };

    init();
  }, [setAuth, setLoading, setError]);

  if (isLoading) {
    return <Loading />;
  }

  // Show error if authentication failed
  if (error) {
    // Check if the error is about not being in any groups
    const isGroupMembershipError = errorDetail?.includes('not currently a member of any groups');
    const isInitDataError = errorDetail?.includes('Chat ID not found in initData') ||
                            errorDetail?.includes('No Telegram authentication');

    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center max-w-md p-6">
          <h1 className="text-3xl font-bold mb-4 gradient-text">Nexus</h1>
          <p className="text-red-400 mb-2">{error}</p>

          {isGroupMembershipError ? (
            <div className="bg-dark-800 rounded-lg p-4 mb-4 text-left">
              <p className="text-dark-300 text-sm mb-2">
                You need to add the bot to a group before using the Mini App:
              </p>
              <ol className="text-dark-400 text-sm list-decimal list-inside space-y-1">
                <li>Add the bot to one of your groups</li>
                <li>Send any message in the group</li>
                <li>Open the Mini App from the group</li>
              </ol>
            </div>
          ) : isInitDataError ? (
            <div className="bg-dark-800 rounded-lg p-4 mb-4 text-left">
              <p className="text-dark-300 text-sm mb-2">
                The Mini App works best when opened from a group:
              </p>
              <ol className="text-dark-400 text-sm list-decimal list-inside space-y-1">
                <li>Go to a group with the bot</li>
                <li>Click the menu button (⋮ or ⋯)</li>
                <li>Select "Mini App" or "🚀 Mini App"</li>
              </ol>
              <p className="text-dark-500 text-xs mt-2">
                Note: Telegram doesn&apos;t provide full authentication data in private chats.
              </p>
            </div>
          ) : errorDetail ? (
            <div className="bg-dark-800 rounded-lg p-4 mb-4 text-left">
              <p className="text-dark-300 text-sm mb-2">Error details:</p>
              <pre className="text-dark-400 text-xs font-mono whitespace-pre-wrap">{errorDetail}</pre>
            </div>
          ) : null}

          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
          >
            Retry
          </button>

          {/* Debug Export Button - Only in development */}
          {import.meta.env.DEV && (
            <button
              onClick={() => {
                const report = enhancedDebug.generateReport();
                console.log(report);
                alert('Debug report printed to console');
              }}
              className="mt-4 ml-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-sm transition-colors"
            >
              Debug Report
            </button>
          )}
        </div>
      </div>
    );
  }

  // Check if opened from a specific group
  // Use the resolved Database Group ID for navigation
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={
          isAuthenticated ? (
            dbGroupId ? <Navigate to={`/admin/${dbGroupId}`} /> : <Dashboard />
          ) : (
            <div className="flex items-center justify-center h-screen">
              <div className="text-center max-w-md p-6">
                <h1 className="text-3xl font-bold mb-4 gradient-text">Nexus</h1>
                <p className="text-dark-400 mb-4">Open this Mini App from Telegram</p>
                <div className="bg-dark-800 rounded-lg p-4 mb-4 text-left">
                  <p className="text-dark-300 text-sm mb-2">To use the Mini App:</p>
                  <ol className="text-dark-400 text-sm list-decimal list-inside space-y-1">
                    <li>Add the bot to a Telegram group</li>
                    <li>Send any message in the group</li>
                    <li>Open the Mini App from the group menu</li>
                  </ol>
                </div>
                <p className="text-dark-500 text-xs">Or check that your session hasn&apos;t expired</p>
              </div>
            </div>
          )
        } />
        <Route path="/help" element={<Help />} />
        <Route path="/profile/:groupId" element={<MemberProfile />} />

        {/* Admin Dashboard Routes - All use Database Group ID */}
        <Route path="/admin/:groupId" element={<AdminDashboard />} />
        <Route path="/admin/:groupId/modules" element={<Modules />} />
        <Route path="/admin/:groupId/members" element={<Members />} />
        <Route path="/admin/:groupId/analytics" element={<Analytics />} />
        <Route path="/admin/:groupId/scheduler" element={<Scheduler />} />
        <Route path="/admin/:groupId/economy" element={<Economy />} />
        <Route path="/admin/:groupId/settings" element={<Settings />} />
        <Route path="/admin/:groupId/bot-builder" element={<BotBuilder />} />
        <Route path="/admin/:groupId/advanced" element={<AdvancedFeatures />} />

        {/* New Feature Routes */}
        <Route path="/admin/:groupId/moderation" element={<ModerationQueue />} />
        <Route path="/admin/:groupId/notes-filters" element={<NotesAndFilters />} />
        <Route path="/admin/:groupId/locks" element={<Locks />} />
        <Route path="/admin/:groupId/antispam" element={<AntiSpam />} />
        <Route path="/admin/:groupId/rules-greetings" element={<RulesAndGreetings />} />
        <Route path="/admin/:groupId/import-export" element={<ImportExport />} />
        <Route path="/admin/:groupId/custom-bot" element={<CustomBotToken />} />
        <Route path="/admin/:groupId/integrations" element={<Integrations />} />

        {/* New Unified Routes */}
        <Route path="/admin/:groupId/security" element={<SecurityCenter />} />
        <Route path="/admin/:groupId/polls" element={<PollsCenter />} />

        {/* New Hubs - High Priority */}
        <Route path="/admin/:groupId/gamification" element={<GamificationHub />} />
        <Route path="/admin/:groupId/community" element={<CommunityHub />} />
        <Route path="/admin/:groupId/games" element={<GamesHub />} />

        {/* New Hubs - Medium Priority */}
        <Route path="/admin/:groupId/broadcast" element={<BroadcastCenter />} />
        <Route path="/admin/:groupId/automation" element={<AutomationCenter />} />

        {/* New Hubs - Low Priority */}
        <Route path="/admin/:groupId/formatting" element={<FormattingTools />} />
        <Route path="/admin/:groupId/search" element={<AdvancedSearch />} />

        {/* Message Graveyard */}
        <Route path="/admin/:groupId/graveyard" element={<Graveyard />} />

        {/* Group Intelligence */}
        <Route path="/admin/:groupId/intelligence" element={<GroupIntelligence />} />
        <Route path="/admin/:groupId/automation-enhanced" element={<AutomationCenterEnhanced />} />
      </Routes>
    </MainLayout>
  );
}

export default App
