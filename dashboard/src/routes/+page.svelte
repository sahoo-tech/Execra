<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { wsService } from '$lib/websocket.svelte';
  import type { ActionRecord } from '$lib/websocket.svelte';

  let history = $state<ActionRecord[]>([]);
  let isLoadingHistory = $state(true);
  let historyError = $state<string | null>(null);
  let isSendingAction = $state(false);
  let isUndoingAction = $state(false);

  // Form inputs for simulating a new action
  let simType = $state('user_click');
  let simDesc = $state('Clicked dashboard simulation button');
  let simDomain = $state<'digital' | 'physical'>('digital');
  let simWasGuided = $state(false);
  let simConfidence = $state(0.9);

  // Fetch initial history from GET /api/v1/actions
  async function fetchHistory() {
    try {
      isLoadingHistory = true;
      historyError = null;
      const res = await fetch('http://127.0.0.1:8000/api/v1/actions?limit=25');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      history = data.actions || [];
    } catch (e: any) {
      console.error('Failed to fetch history:', e);
      historyError = e.message || 'Failed to connect to backend API';
    } finally {
      isLoadingHistory = false;
    }
  }

  // Simulate logging a new action via POST /api/v1/actions
  async function handleSimulateAction(e: SubmitEvent) {
    e.preventDefault();
    if (isSendingAction) return;

    try {
      isSendingAction = true;
      const payload: ActionRecord = {
        id: `act_${Date.now()}`,
        session_id: `sess_${Date.now().toString().slice(-4)}`,
        timestamp: new Date().toISOString(),
        type: simType,
        description: simDesc,
        domain: simDomain,
        was_guided: simWasGuided,
        guidance_confidence: simWasGuided ? simConfidence : null
      };

      const res = await fetch('http://127.0.0.1:8000/api/v1/actions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      
      // Reset inputs slightly
      simDesc = `Clicked dashboard simulation button ${Math.floor(Math.random() * 100)}`;
    } catch (err) {
      console.error('Failed to simulate action:', err);
    } finally {
      isSendingAction = false;
    }
  }

  // Undo the last action via POST /api/v1/actions/undo
  async function handleUndoLast() {
    if (isUndoingAction) return;
    try {
      isUndoingAction = true;
      const res = await fetch('http://127.0.0.1:8000/api/v1/actions/undo', {
        method: 'POST'
      });
      if (res.status === 409) {
        alert('Nothing to undo! Action log is empty.');
        return;
      }
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      
      const data = await res.json();
      const undoneId = data.action_undone?.id;
      
      // Update local states by filtering out the undone action
      if (undoneId) {
        history = history.filter(item => item.id !== undoneId);
        wsService.events = wsService.events.filter(item => item.id !== undoneId);
      }
    } catch (err) {
      console.error('Failed to undo last action:', err);
    } finally {
      isUndoingAction = false;
    }
  }

  onMount(() => {
    wsService.connect();
    fetchHistory();
  });

  onDestroy(() => {
    wsService.disconnect();
  });

  // Reactive derivation combining WebSocket events and initial history log
  const allActions = $derived(() => {
    const seen = new Set<string>();
    const combined: ActionRecord[] = [];
    
    // WebSockets first
    for (const item of wsService.events) {
      if (!seen.has(item.id)) {
        seen.add(item.id);
        combined.push(item);
      }
    }
    
    // Persisted history second
    for (const item of history) {
      if (!seen.has(item.id)) {
        seen.add(item.id);
        combined.push(item);
      }
    }
    
    return combined;
  });

  // Stats derivations
  const totalCount = $derived(allActions().length);
  const digitalCount = $derived(allActions().filter(a => a.domain === 'digital').length);
  const physicalCount = $derived(allActions().filter(a => a.domain === 'physical').length);
  
  const guidanceStats = $derived(() => {
    const guided = allActions().filter(a => a.was_guided);
    const rate = totalCount > 0 ? Math.round((guided.length / totalCount) * 100) : 0;
    
    const confidences = guided.map(a => a.guidance_confidence || 0).filter(c => c > 0);
    const avgConfidence = confidences.length > 0 
      ? Math.round((confidences.reduce((sum, val) => sum + val, 0) / confidences.length) * 100) 
      : 0;

    return { rate, avgConfidence };
  });

  function formatTime(isoString: string) {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '';
    }
  }

  function formatDate(isoString: string) {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  }
</script>

<div class="min-h-screen bg-[#0b1020] text-[#e5e7eb] flex flex-col font-mono text-sm antialiased selection:bg-emerald-500/30 selection:text-emerald-300">
  <!-- Top Navigation Status Bar -->
  <header class="border-b border-slate-800 bg-[#111827]/85 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-40">
    <div class="flex items-center space-x-3">
      <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
      <h1 class="text-lg font-bold tracking-wider text-white">
        EXECRA <span class="text-slate-500">//</span> MONITORING_LAYER
      </h1>
    </div>

    <div class="flex items-center space-x-6">
      <!-- WS Status Indicator -->
      <div class="flex items-center space-x-3 bg-slate-900 border border-slate-800 px-4 py-1.5 rounded-md">
        <span class="text-xs text-slate-500 uppercase tracking-widest">Websocket</span>
        <div class="flex items-center space-x-2">
          {#if wsService.status === 'CONNECTED'}
            <span class="h-2.5 w-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981] animate-[pulse_2s_infinite]"></span>
            <span class="text-xs font-semibold text-emerald-400">CONNECTED</span>
          {:else if wsService.status === 'RECONNECTING'}
            <span class="h-2.5 w-2.5 rounded-full bg-amber-500 shadow-[0_0_8px_#f59e0b] animate-[pulse_1s_infinite]"></span>
            <span class="text-xs font-semibold text-amber-400">RECONNECTING...</span>
          {:else}
            <span class="h-2.5 w-2.5 rounded-full bg-red-500 shadow-[0_0_8px_#ef4444] animate-[pulse_2s_infinite]"></span>
            <span class="text-xs font-semibold text-red-400">DISCONNECTED</span>
          {/if}
        </div>
      </div>

      <button 
        onclick={() => wsService.connect()} 
        class="bg-slate-800 border border-slate-700 hover:bg-slate-700 active:bg-slate-900 text-xs px-3 py-1.5 rounded-md font-semibold text-slate-300 transition duration-150 ease-in-out cursor-pointer"
        aria-label="Reconnect connection manually"
      >
        RECONNECT
      </button>
    </div>
  </header>

  <main class="flex-grow p-6 max-w-7xl w-full mx-auto space-y-6">
    <!-- Operational Statistics Cards Grid -->
    <section class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-[#111827] border border-slate-800 p-5 rounded-lg flex flex-col justify-between hover:border-slate-700 transition duration-150">
        <span class="text-xs text-slate-500 uppercase tracking-widest font-semibold">Total Actions Captured</span>
        <div class="flex items-baseline space-x-2 mt-2">
          <span class="text-3xl font-bold text-white">{totalCount}</span>
          <span class="text-xs text-slate-500">records</span>
        </div>
        <div class="mt-3 text-xs text-slate-400 border-t border-slate-800/80 pt-2 flex justify-between">
          <span>Digital: <strong class="text-slate-300">{digitalCount}</strong></span>
          <span>Physical: <strong class="text-slate-300">{physicalCount}</strong></span>
        </div>
      </div>

      <div class="bg-[#111827] border border-slate-800 p-5 rounded-lg flex flex-col justify-between hover:border-slate-700 transition duration-150">
        <span class="text-xs text-slate-500 uppercase tracking-widest font-semibold">AI Guidance Rate</span>
        <div class="flex items-baseline space-x-2 mt-2">
          <span class="text-3xl font-bold text-emerald-400">{guidanceStats().rate}%</span>
          <span class="text-xs text-slate-500">of total</span>
        </div>
        <div class="mt-3 text-xs text-slate-400 border-t border-slate-800/80 pt-2 flex justify-between">
          <span>Avg Confidence: <strong class="text-emerald-400">{guidanceStats().avgConfidence}%</strong></span>
        </div>
      </div>

      <div class="bg-[#111827] border border-slate-800 p-5 rounded-lg flex flex-col justify-between hover:border-slate-700 transition duration-150">
        <span class="text-xs text-slate-500 uppercase tracking-widest font-semibold">Operational State</span>
        <div class="flex items-baseline space-x-2 mt-2">
          <span class="text-3xl font-bold text-white">PASSIVE</span>
          <span class="text-xs text-slate-500">mode</span>
        </div>
        <div class="mt-3 text-xs text-slate-400 border-t border-slate-800/80 pt-2 flex justify-between">
          <span>Active Domain: <strong class="text-slate-300">digital</strong></span>
        </div>
      </div>
    </section>

    <!-- Main Workspace Split Panel -->
    <section class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      
      <!-- Left Panel: Live Execution Log Timeline (7/12 cols) -->
      <div class="lg:col-span-7 bg-[#111827] border border-slate-800 rounded-lg flex flex-col h-[650px] overflow-hidden">
        <div class="border-b border-slate-800 px-5 py-4 flex items-center justify-between bg-slate-900/50">
          <div class="flex items-center space-x-2">
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
            <h2 class="font-bold text-sm tracking-wider uppercase text-white">Realtime Event Timeline</h2>
          </div>
          <span class="text-xs px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 tracking-wider">LIVE STREAMING</span>
        </div>

        <!-- Scrollable Action Feed -->
        <div class="flex-grow overflow-y-auto p-5 space-y-4">
          {#if allActions().length === 0}
            {#if isLoadingHistory}
              <div class="h-full flex flex-col items-center justify-center text-slate-500 space-y-2">
                <span class="border-2 border-slate-700 border-t-emerald-500 rounded-full h-6 w-6 animate-spin"></span>
                <span class="text-xs uppercase tracking-wider">Fetching execution logs...</span>
              </div>
            {:else}
              <div class="h-full flex flex-col items-center justify-center text-slate-600 border-2 border-dashed border-slate-800 rounded-lg p-6 text-center">
                <svg class="h-8 w-8 mb-2 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span class="text-xs font-semibold uppercase tracking-wider">No execution actions recorded yet</span>
                <p class="text-[11px] text-slate-500 mt-1 max-w-[280px]">Run uvicorn and submit actions or use the simulator panel on the right.</p>
              </div>
            {/if}
          {:else}
            <!-- Timeline Line Grid -->
            <div class="relative border-l border-slate-800 pl-6 ml-3 space-y-6">
              {#each allActions() as action, index (action.id)}
                <div class="relative group">
                  <!-- Timeline Node Pin -->
                  <span class="absolute -left-[31px] top-1.5 h-2.5 w-2.5 rounded-full border border-[#111827] group-hover:scale-110 transition duration-150 {action.was_guided ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]' : 'bg-slate-700'}"></span>

                  <div class="bg-[#0b1020]/60 border border-slate-800/80 rounded-lg p-4 hover:border-slate-700 transition duration-150">
                    <div class="flex items-center justify-between text-xs mb-1.5">
                      <div class="flex items-center space-x-2">
                        <span class="text-slate-300 font-bold text-[13px]">{action.type}</span>
                        <span class="text-[10px] text-slate-500 tracking-tighter">({action.id})</span>
                      </div>
                      <div class="flex items-center space-x-2 text-[10px] text-slate-500">
                        <span>{formatDate(action.timestamp)}</span>
                        <span>{formatTime(action.timestamp)}</span>
                      </div>
                    </div>

                    <p class="text-xs text-slate-300 leading-relaxed mb-3">{action.description}</p>

                    <!-- Bottom badges -->
                    <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-900/50">
                      <!-- Domain Pill -->
                      <span class="text-[9px] uppercase tracking-wider px-2 py-0.5 rounded font-semibold border {action.domain === 'digital' ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' : 'bg-orange-500/10 border-orange-500/20 text-orange-400'}">
                        {action.domain}
                      </span>

                      <!-- Guidance Pill -->
                      {#if action.was_guided}
                        <span class="text-[9px] uppercase tracking-wider px-2 py-0.5 rounded font-semibold bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                          Guided ({action.guidance_confidence ? Math.round(action.guidance_confidence * 100) : 0}%)
                        </span>
                      {/if}

                      <span class="text-[9px] text-slate-500 font-mono">session_id: {action.session_id}</span>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <!-- Right Panel: Simulator & persistent Database logs (5/12 cols) -->
      <div class="lg:col-span-5 space-y-6">
        
        <!-- Live Action Simulator Card -->
        <div class="bg-[#111827] border border-slate-800 rounded-lg p-5">
          <h2 class="font-bold text-sm tracking-wider uppercase text-white mb-4 border-b border-slate-800 pb-2.5">
            LOG_ACTION_SIMULATOR
          </h2>
          
          <form onsubmit={handleSimulateAction} class="space-y-4">
            <div>
              <label for="action-type" class="block text-[11px] text-slate-500 uppercase tracking-widest font-semibold mb-1.5">Action Type</label>
              <select 
                id="action-type"
                bind:value={simType} 
                class="w-full bg-[#0b1020] border border-slate-800 text-slate-300 text-xs px-3 py-2 rounded-md focus:border-slate-700 outline-none"
              >
                <option value="user_click">user_click</option>
                <option value="keypress">keypress</option>
                <option value="api_trigger">api_trigger</option>
                <option value="ocr_detection">ocr_detection</option>
                <option value="plugin_firing">plugin_firing</option>
              </select>
            </div>

            <div>
              <label for="action-description" class="block text-[11px] text-slate-500 uppercase tracking-widest font-semibold mb-1.5">Description</label>
              <input 
                id="action-description"
                type="text" 
                bind:value={simDesc} 
                placeholder="Describe simulated action..."
                required
                class="w-full bg-[#0b1020] border border-slate-800 text-slate-300 text-xs px-3 py-2 rounded-md focus:border-slate-700 outline-none"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label for="action-domain" class="block text-[11px] text-slate-500 uppercase tracking-widest font-semibold mb-1.5">Domain</label>
                <select 
                  id="action-domain"
                  bind:value={simDomain} 
                  class="w-full bg-[#0b1020] border border-slate-800 text-slate-300 text-xs px-3 py-2 rounded-md focus:border-slate-700 outline-none"
                >
                  <option value="digital">digital</option>
                  <option value="physical">physical</option>
                </select>
              </div>

              <div>
                <label for="action-guidance" class="block text-[11px] text-slate-500 uppercase tracking-widest font-semibold mb-1.5">Guidance</label>
                <select 
                  id="action-guidance"
                  bind:value={simWasGuided} 
                  class="w-full bg-[#0b1020] border border-slate-800 text-slate-300 text-xs px-3 py-2 rounded-md focus:border-slate-700 outline-none"
                >
                  <option value={false}>No Guidance</option>
                  <option value={true}>AI Guided</option>
                </select>
              </div>
            </div>

            {#if simWasGuided}
              <div class="bg-[#0b1020]/80 p-3 rounded border border-slate-800/80">
                <div class="flex justify-between text-[11px] mb-1">
                  <span class="text-slate-500 uppercase font-semibold">Guidance Confidence</span>
                  <span class="text-emerald-400 font-bold">{Math.round(simConfidence * 100)}%</span>
                </div>
                <input 
                  type="range" 
                  min="0.1" 
                  max="1.0" 
                  step="0.05" 
                  bind:value={simConfidence} 
                  class="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500" 
                />
              </div>
            {/if}

            <button 
              type="submit" 
              disabled={isSendingAction}
              class="w-full bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 active:bg-emerald-500/30 text-emerald-400 font-bold uppercase tracking-widest text-xs py-2 rounded-md transition duration-150 cursor-pointer disabled:opacity-50"
            >
              {#if isSendingAction}
                SENDING_PAYLOAD...
              {:else}
                BROADCAST SIMULATED ACTION
              {/if}
            </button>
          </form>
        </div>

        <!-- Controls panel card -->
        <div class="bg-[#111827] border border-slate-800 rounded-lg p-5">
          <h2 class="font-bold text-sm tracking-wider uppercase text-white mb-4 border-b border-slate-800 pb-2.5">
            ADMIN_CONTROLS
          </h2>

          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 bg-[#0b1020]/60 border border-slate-800 rounded-md">
              <div class="text-xs">
                <p class="font-bold text-slate-300">Undo Last Action</p>
                <p class="text-[10px] text-slate-500 mt-0.5">Removes last action from logger</p>
              </div>
              <button 
                onclick={handleUndoLast} 
                disabled={isUndoingAction}
                class="bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 text-xs px-3.5 py-1.5 rounded font-semibold transition cursor-pointer disabled:opacity-50"
              >
                UNDO LAST
              </button>
            </div>

            <div class="flex items-center justify-between p-3 bg-[#0b1020]/60 border border-slate-800 rounded-md">
              <div class="text-xs">
                <p class="font-bold text-slate-300">Reload Log History</p>
                <p class="text-[10px] text-slate-500 mt-0.5">Fetch recent 25 persistent records</p>
              </div>
              <button 
                onclick={fetchHistory} 
                disabled={isLoadingHistory}
                class="bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 text-xs px-3.5 py-1.5 rounded font-semibold transition cursor-pointer disabled:opacity-50"
              >
                REFRESH DB
              </button>
            </div>
          </div>
        </div>

        <!-- System state logs card -->
        <div class="bg-[#111827] border border-slate-800 rounded-lg p-5">
          <h2 class="font-bold text-sm tracking-wider uppercase text-white mb-4 border-b border-slate-800 pb-2.5">
            HARDWARE_SUMMARY
          </h2>
          <div class="space-y-2 text-xs text-slate-400">
            <div class="flex justify-between">
              <span>HOST_IP</span>
              <span class="text-white">127.0.0.1:8000</span>
            </div>
            <div class="flex justify-between">
              <span>ACTIVE_PERCEPTION_MODULES</span>
              <span class="text-white">ocr, screen_capture</span>
            </div>
            <div class="flex justify-between">
              <span>LLM_MODEL_TARGET</span>
              <span class="text-white">gpt-4o</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</div>
