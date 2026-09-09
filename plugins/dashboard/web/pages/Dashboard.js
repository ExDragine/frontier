// 总览页面
const DashboardPage = {
    template: `
        <div class="space-y-6">
            <h1 class="text-2xl font-bold text-gray-800">系统总览</h1>
            
            <!-- 统计卡片 -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm text-gray-500">运行时间</p>
                            <p class="text-2xl font-bold text-gray-800 mt-1">{{ formatUptime(overview.uptime_seconds) }}</p>
                        </div>
                        <div class="text-4xl">⏱️</div>
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm text-gray-500">消息总数</p>
                            <p class="text-2xl font-bold text-gray-800 mt-1">{{ overview.database?.message_count || 0 }}</p>
                        </div>
                        <div class="text-4xl">💬</div>
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm text-gray-500">用户数</p>
                            <p class="text-2xl font-bold text-gray-800 mt-1">{{ overview.database?.user_count || 0 }}</p>
                        </div>
                        <div class="text-4xl">👥</div>
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm text-gray-500">定时任务</p>
                            <p class="text-2xl font-bold text-gray-800 mt-1">{{ overview.database?.task_count || 0 }}</p>
                        </div>
                        <div class="text-4xl">⏰</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-lg font-semibold text-gray-800">Agent 用量</h2>
                <p class="text-xs text-gray-500 mt-1 mb-4">本次启动以来已结束任务的累计统计，含主模型和本地子代理；重启后重新计数。</p>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                        <p class="text-sm text-gray-500">任务 / 达到预算上限</p>
                        <p class="text-xl font-semibold">{{ overview.agent_usage?.runs || 0 }} / {{ overview.agent_usage?.budget_exceeded_runs || 0 }}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">模型 / 工具调用</p>
                        <p class="text-xl font-semibold">{{ overview.agent_usage?.model_calls || 0 }} / {{ overview.agent_usage?.tool_calls || 0 }}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">输入 / 输出 token</p>
                        <p class="text-xl font-semibold">{{ overview.agent_usage?.input_tokens || 0 }} / {{ overview.agent_usage?.output_tokens || 0 }}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">缓存命中 / 推理 token</p>
                        <p class="text-xl font-semibold">{{ overview.agent_usage?.cache_read_tokens || 0 }} / {{ overview.agent_usage?.reasoning_tokens || 0 }}</p>
                    </div>
                </div>
                <p v-if="overview.agent_usage?.usage_missing_calls" class="text-sm text-amber-700 mt-3">
                    有 {{ overview.agent_usage.usage_missing_calls }} 次模型调用未返回用量，token 统计可能不完整。
                </p>
            </div>

            <div v-if="overview.agent_sessions" class="bg-white rounded-lg shadow p-6">
                <div class="flex justify-between items-center mb-2">
                    <h2 class="text-lg font-semibold text-gray-800">会话缓存</h2>
                    <span class="text-sm text-gray-500">{{ overview.agent_sessions.enabled ? '已启用' : '已关闭' }}</span>
                </div>
                <p class="text-xs text-gray-500 mb-4">连续对话复用状态，空闲后释放；重启后从聊天记录重建。</p>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                        <p class="text-sm text-gray-500">常驻会话</p>
                        <p class="text-xl font-semibold">{{ overview.agent_sessions.sessions || 0 }}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">复用 / 重建</p>
                        <p class="text-xl font-semibold">{{ overview.agent_sessions.hot_hits || 0 }} / {{ overview.agent_sessions.cold_starts || 0 }}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">缓存占用上界</p>
                        <p class="text-xl font-semibold">{{ ((overview.agent_sessions.serialized_bytes_upper_bound || 0) / 1048576).toFixed(1) }} MiB</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">快照冲突回退</p>
                        <p class="text-xl font-semibold">{{ overview.agent_sessions.snapshot_conflict || 0 }}</p>
                    </div>
                </div>
            </div>

            <!-- 系统信息 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white rounded-lg shadow p-6">
                    <h2 class="text-lg font-semibold text-gray-800 mb-4">模型配置</h2>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-600">基础模型</span>
                            <span class="font-mono text-sm">{{ overview.models?.basic_model }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">高级模型</span>
                            <span class="font-mono text-sm">{{ overview.models?.advan_model }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">绘图模型</span>
                            <span class="font-mono text-sm">{{ overview.models?.paint_model }}</span>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <h2 class="text-lg font-semibold text-gray-800 mb-4">功能状态</h2>
                    <div class="space-y-3">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-600">Agent 模块</span>
                            <span :class="overview.features?.agent_module_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
                                  class="px-2 py-1 rounded text-sm">
                                {{ overview.features?.agent_module_enabled ? '已启用' : '已禁用' }}
                            </span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-600">绘图模块</span>
                            <span :class="overview.features?.paint_module_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
                                  class="px-2 py-1 rounded text-sm">
                                {{ overview.features?.paint_module_enabled ? '已启用' : '已禁用' }}
                            </span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-600">记忆系统</span>
                            <span :class="overview.features?.memory_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
                                  class="px-2 py-1 rounded text-sm">
                                {{ overview.features?.memory_enabled ? '已启用' : '已禁用' }}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Agent 能力</span>
                            <span class="font-medium">{{ overview.features?.agent_capability }}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 系统资源 -->
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-lg font-semibold text-gray-800 mb-4">系统资源</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <div class="flex justify-between mb-2">
                            <span class="text-gray-600">内存使用</span>
                            <span class="font-medium">{{ system.memory?.percent }}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div :style="{width: system.memory?.percent + '%'}"
                                 class="bg-blue-500 h-2 rounded-full transition-all"></div>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">
                            {{ system.memory?.used_mb }} MB / {{ system.memory?.total_mb }} MB
                        </p>
                    </div>
                    
                    <div>
                        <div class="flex justify-between mb-2">
                            <span class="text-gray-600">磁盘使用</span>
                            <span class="font-medium">{{ system.disk?.percent }}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div :style="{width: system.disk?.percent + '%'}"
                                 class="bg-green-500 h-2 rounded-full transition-all"></div>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">
                            {{ system.disk?.used_gb }} GB / {{ system.disk?.total_gb }} GB
                        </p>
                    </div>
                    
                    <div>
                        <p class="text-gray-600 mb-2">进程内存</p>
                        <p class="text-2xl font-bold text-gray-800">{{ system.memory?.process_mb }} MB</p>
                        <p class="text-xs text-gray-500 mt-1">
                            Python {{ system.python_version }}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    `,
    setup() {
        const { ref, onMounted, onUnmounted } = Vue;
        const overview = ref({});
        const system = ref({});
        let interval = null;
        
        const fetchData = async () => {
            try {
                const [overviewData, systemData] = await Promise.all([
                    ApiClient.get('/status/overview'),
                    ApiClient.get('/status/system')
                ]);
                overview.value = overviewData;
                system.value = systemData;
            } catch (err) {
                showToast('加载数据失败: ' + err.message, 'error');
            }
        };
        
        const formatUptime = (seconds) => {
            if (!seconds) return '0秒';
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            const parts = [];
            if (days > 0) parts.push(`${days}天`);
            if (hours > 0) parts.push(`${hours}小时`);
            if (mins > 0) parts.push(`${mins}分钟`);
            return parts.join(' ') || '少于1分钟';
        };
        
        onMounted(() => {
            fetchData();
            interval = setInterval(fetchData, 30000);
        });
        
        onUnmounted(() => {
            if (interval) clearInterval(interval);
        });
        
        return { overview, system, formatUptime };
    }
};
